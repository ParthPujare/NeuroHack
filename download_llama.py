import os
import requests
import sys
from urllib.parse import urlparse, parse_qs

# The user provided: https://llama3-2-lightweight.llamameta.net/*?Policy=...
# The * indicates a policy resource, but we need the actual file paths.
# Meta Llama downloads usually involve a `checklist.chk` at the root.
# Let's try to access the root without the wildcard.

BASE_URL = "https://llama3-2-lightweight.llamameta.net"
# We need to construct the URL for specific files using the query params.
QUERY_STRING = "Policy=eyJTdGF0ZW1lbnQiOlt7InVuaXF1ZV9oYXNoIjoibzMzaXQyYmtsbWxwYmdpMnB4b2kwZDB1IiwiUmVzb3VyY2UiOiJodHRwczpcL1wvbGxhbWEzLTItbGlnaHR3ZWlnaHQubGxhbWFtZXRhLm5ldFwvKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc3MDkxMDk5MH19fV19&Signature=UecXy6GnwawsyOsiIbeBFcwO4pK-vnMrBy%7Ezh0l0RNL3DNSutyT4ekYnShF%7EQEiPGtseW7HudmZtd5OLZtM7d8YZYtN4eDNmVlq6MbGUo7fWJTe904fK9bQnyUWaDaFhi8KVDPQCcaV1iuq7fmD%7EiJxmtVhxn-cCI1%7EFYs0dFA8xQix3RIxdcZaHHu307rX6FcyHf%7Ee-a8N0nPjbE4cuBfqV%7E4lO9rXRuhDEIIhQc6dl%7Ewxkr4M2wO2C1L2jOb-lJylNNrSYdbVjn4d-HoodDd5k0ITtYvMUQvabsW1UnDynuGntTI2%7EzPeTqDe57PEwPdwoqFlLA9RBXRdQpbD8ww__&Key-Pair-Id=K15QRJLYKIFSLZ&Download-Request-ID=932753542765553"

TARGET_DIR = "models/llama-3.2-3b"
os.makedirs(TARGET_DIR, exist_ok=True)

def download_file(path):
    # Construct URL: BASE_URL + / + path + ? + QUERY_STRING
    url = f"{BASE_URL}/{path}?{QUERY_STRING}"
    print(f"Downloading {path}...")
    try:
        with requests.get(url, stream=True) as r:
            if r.status_code != 200:
                print(f"Failed to download {path}: {r.status_code} {r.reason}")
                return False
            
            # Save to disk
            local_path = os.path.join(TARGET_DIR, path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded {path}")
        return True
    except Exception as e:
        print(f"Error downloading {path}: {e}")
        return False

# Try common paths for Llama 3.2
# The signed link is for "lightweight" models (1B and 3B).
# Usually structure is:
# /checklist.chk
# /params.json
# /consolidated.00.pth
# /tokenizer.model
#
# OR
# /3B/checklist.chk
# /3B/params.json
# ...

# Let's try the 3B folder structure first as implied by the user's request
files_to_try = [
    "checklist.chk",
    "params.json",
    "tokenizer.model", 
    "consolidated.00.pth",
    "3B/checklist.chk",
    "3B/params.json",
    "3B/consolidated.00.pth",
    "3B/tokenizer.model"
]

success = False
for f in files_to_try:
    if download_file(f):
        success = True

if not success:
    print("Failed to download any files. The URL might be expired or the path structure is different.")

