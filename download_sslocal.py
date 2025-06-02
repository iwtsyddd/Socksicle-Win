import os
import sys
import shutil
import zipfile
import requests
import time 

URL = "https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.23.3/shadowsocks-v1.23.3.x86_64-pc-windows-msvc.zip"
ZIP_FILE = "shadowsocks.zip"
EXE_NAME = "sslocal.exe"
FOLDER_NAME = "shadowsocks-v1.23.3.x86_64-pc-windows-msvc"

def download_file(url, dest):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

try:
    print(f"Downloading {URL} ...")
    download_file(URL, ZIP_FILE)
except Exception as e:
    print(f"Error downloading file: {e}")
    sys.exit(1)

if not os.path.exists(ZIP_FILE):
    print("Error downloading file")
    sys.exit(1)

try:
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(".")
except Exception as e:
    print(f"Error extracting zip: {e}")
    sys.exit(1)

time.sleep(2) 

exe_path = os.path.join(FOLDER_NAME, EXE_NAME)
if not os.path.exists(exe_path):
    sys.exit(1)

shutil.move(exe_path, EXE_NAME)
shutil.rmtree(FOLDER_NAME, ignore_errors=True)
os.remove(ZIP_FILE)
