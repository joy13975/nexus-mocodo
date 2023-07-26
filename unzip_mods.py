import os
from glob import glob
import zipfile
import concurrent.futures
import config

if not os.path.isdir(config.unzip_path):
    os.makedirs(config.unzip_path)

out_dir = os.path.expanduser(config.unzip_path)
src_dirs = config.download_path

files = glob(f'{src_dirs}/*.zip')

def unzip_to_path(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile:
        # This sometimes happens for completely valid zips - not sure why.
        print(f'Could not unzip: {zip_path}')

print(f'Will attempt to unzip {len(files)} files')
with concurrent.futures.ThreadPoolExecutor(8) as executor:
    res = [
        executor.submit(unzip_to_path, f)
        for f in files
    ]
    concurrent.futures.wait(res)

print(f'If any unzip failed, you need to do them manually.')
