import os
import requests
import json
import concurrent.futures
import config

output_dir = config.download_path
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)
with open('collection.json') as f:
    collection = json.load(f)

mods = collection['mods']

def download_from_url(url, save_path):
    if os.path.isfile(save_path):
        print(f'Already downloaded: {save_path}')
        return
    r = requests.get(url, allow_redirects=True)
    if r.status_code != 200:
        return r
    with open(save_path, 'wb') as f:
        f.write(r.content)

def get_dl_url(mod_id, file_id):
    cookies = {
        # You need to acquire your browser cookies once for each collection.
        # 1. Open Chrome inspector or equivalent, and open the Network tab.
        # 2. Attempt to manually download any mod e.g. https://www.nexusmods.com/stardewvalley/mods/5371?tab=files&file_id=56774
        # 3. Search for "Downloads?" for API request to "Downloads?GenerateDownloadUrl"
        # 4. Copy cURL command, and convert to Python code at https://curlconverter.com/
        # Finally, paste the cookies here and optionally the headers below as well
    }
    headers = {
        'authority': r'www.nexusmods.com',
        'accept': r'*/*',
        'accept-language': r'en,ja;q=0.9,zh-TW;q=0.8,zh;q=0.7,zh-CN;q=0.6',
        'content-type': r'application/x-www-form-urlencoded; charset=UTF-8',
        'dnt': r'1',
        'origin': r'https://www.nexusmods.com',
        'referer': rf'https://www.nexusmods.com/stardewvalley/mods/{mod_id}?tab=files&file_id={file_id}',
        'sec-ch-ua': r'"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': r'?0',
        'sec-ch-ua-platform': r'"macOS"',
        'sec-fetch-dest': r'empty',
        'sec-fetch-mode': r'cors',
        'sec-fetch-site': r'same-origin',
        'user-agent': r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-requested-with': r'XMLHttpRequest',
    }
    data = {
        'fid': str(file_id),
        'game_id': '1303',
    }
    r = requests.post(
        'https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl',
        cookies=cookies,
        headers=headers,
        data=data,
    )
    if r.status_code == 200:
        return r.json()['url']
    raise Exception(f'Bad response: {r.status}')
    
def download_mod(mod_info):
    src = mod_info['source']
    mod_name = mod_info['name']
    save_path = f'{output_dir}/' + mod_name + '.zip'
    if 'url' in src:
        url = src['url']
    else:
        url = get_dl_url(src['modId'], src['fileId'])
    print('Attempting to download:', mod_name)
    r = download_from_url(url, save_path)
    if r is not None:
        print(f'Failed to download {mod_name}. Code={r.status_code}; Reason={r.reason}')


with concurrent.futures.ThreadPoolExecutor(8) as executor:
    res = [
        executor.submit(download_mod, mod_info)
        for mod_info in mods
    ]
    concurrent.futures.wait(res)
