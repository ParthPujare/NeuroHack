import os
import requests
from tqdm import tqdm

# Public GGUF repo (Bartowski is a reputable quantizer)
MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
TARGET_DIR = "models"
TARGET_FILE = os.path.join(TARGET_DIR, "Llama-3.2-3B-Instruct-Q4_K_M.gguf")

os.makedirs(TARGET_DIR, exist_ok=True)

def download_file(url, filename):
    print(f"Downloading {filename}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, stream=True, headers=headers)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
        return False
    print("Download complete!")
    return True

if not os.path.exists(TARGET_FILE):
    download_file(MODEL_URL, TARGET_FILE)
else:
    print(f"Model already exists at {TARGET_FILE}")
