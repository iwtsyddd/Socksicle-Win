import requests

URL = "https://github.com/iwtsyddd/Socksicle-Win/releases/download/dependencies/sslocal.exe"
EXE_NAME = "sslocal.exe"

def download_file(url, dest):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

try:
    print(f"Downloading {URL} ...")
    download_file(URL, EXE_NAME)
    print("Download completed.")
except Exception as e:
    print(f"Error downloading file: {e}")
