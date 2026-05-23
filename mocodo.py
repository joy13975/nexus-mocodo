#!/usr/bin/env python3
"""Download a list of Nexus mod URLs and install them into a Mods directory.

Usage:
    uv run python mocodo.py --mods-file mods.txt --dest "<path/to/Mods>"

`mods.txt` is newline-delimited Nexus mod URLs. Lines starting with `#` and blanks
are ignored. URLs may or may not carry `?file_id=...`; if missing, the latest
main file is fetched from the mod's files page.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from cookies import cookies
except ImportError:
    sys.exit(
        "ERROR: cookies.py not found.\n"
        "  cp cookies.example.py cookies.py   # then paste your nexus cookies"
    )

GAME_IDS = {"stardewvalley": "1303"}
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def parse_url(url: str) -> tuple[str, int, int | None]:
    p = urlparse(url)
    parts = p.path.strip("/").split("/")
    if len(parts) < 3 or parts[1] != "mods":
        raise ValueError(f"Unexpected Nexus URL shape: {url}")
    game = parts[0]
    mod_id = int(parts[2])
    q = parse_qs(p.query)
    file_id = int(q["file_id"][0]) if "file_id" in q else None
    return game, mod_id, file_id


def make_session() -> requests.Session:
    s = requests.Session()
    s.cookies.update(cookies)
    s.headers.update({"User-Agent": UA, "accept-language": "en"})
    return s


def resolve_main_file_id(s: requests.Session, game: str, mod_id: int) -> int:
    url = f"https://www.nexusmods.com/{game}/mods/{mod_id}?tab=files"
    r = s.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"GET {url} -> {r.status_code} (cookies likely expired or insufficient)"
        )
    soup = BeautifulSoup(r.text, "html.parser")
    container = soup.find(id="file-container-main-files")
    target = container if container else soup
    el = target.find(attrs={"data-id": re.compile(r"^\d+$")})
    if not el:
        raise RuntimeError(f"No file id found on {url}")
    return int(el["data-id"])


def get_download_url(s: requests.Session, game: str, mod_id: int, file_id: int) -> str:
    game_id = GAME_IDS.get(game)
    if not game_id:
        raise ValueError(f"Unknown game slug {game!r}; add it to GAME_IDS.")
    headers = {
        "referer": f"https://www.nexusmods.com/{game}/mods/{mod_id}?tab=files&file_id={file_id}",
        "origin": "https://www.nexusmods.com",
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"fid": str(file_id), "game_id": game_id}
    r = s.post(
        "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl",
        headers=headers,
        data=data,
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"GenerateDownloadUrl -> {r.status_code}: {r.text[:200]}")
    return r.json()["url"]


def download_file(s: requests.Session, url: str, dest: str) -> None:
    with s.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        tmp = dest + ".part"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
        os.replace(tmp, dest)


def install_zip(zip_path: str, dest_dir: str) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)


def process(s: requests.Session, url: str, cache_dir: str, dest_dir: str) -> str:
    game, mod_id, file_id = parse_url(url)
    if file_id is None:
        file_id = resolve_main_file_id(s, game, mod_id)
        print(f"[mod {mod_id}] resolved main file_id={file_id}")
    dl_url = get_download_url(s, game, mod_id, file_id)
    fname = os.path.basename(urlparse(dl_url).path) or f"mod_{mod_id}_{file_id}.zip"
    zip_path = os.path.join(cache_dir, fname)
    if os.path.exists(zip_path):
        print(f"[mod {mod_id}] cached: {fname}")
    else:
        print(f"[mod {mod_id}] downloading: {fname}")
        download_file(s, dl_url, zip_path)
    print(f"[mod {mod_id}] installing -> {dest_dir}")
    install_zip(zip_path, dest_dir)
    return fname


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mods-file", required=True, help="newline-delimited Nexus mod URLs")
    ap.add_argument("--dest", required=True, help="target Mods/ directory")
    ap.add_argument("--cache-dir", default="downloaded_mods", help="where to keep downloaded zips")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    if not cookies:
        sys.exit("ERROR: cookies.py is empty. Paste your nexusmods.com cookies into it.")

    dest = os.path.expanduser(args.dest)
    if not os.path.isdir(dest):
        sys.exit(f"ERROR: --dest does not exist: {dest}")
    os.makedirs(args.cache_dir, exist_ok=True)

    with open(args.mods_file) as f:
        urls = [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    if not urls:
        sys.exit(f"ERROR: no URLs found in {args.mods_file}")
    print(f"Processing {len(urls)} mods -> {dest}")

    s = make_session()
    failures: list[tuple[str, BaseException]] = []
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(process, s, u, args.cache_dir, dest): u for u in urls}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                fut.result()
            except Exception as e:
                failures.append((u, e))
                print(f"FAILED {u}: {e}")

    if failures:
        print(f"\n{len(failures)} failure(s):")
        for u, e in failures:
            print(f"  {u}\n    -> {e}")
        return 1
    print("\nAll mods installed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
