# updater.py — checagem robusta da versão remota (repo público/privado, main/master)
import os
import base64
import requests

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_VERSION_FILE = os.path.join(APP_DIR, "VERSION")

OWNER = "pedromartellitech"
REPO  = "lana-modas-updates"
BRANCH = os.environ.get("LANA_UPDATE_BRANCH", "main")  # troque se quiser outro branch
GITHUB_TOKEN = (os.environ.get("GITHUB_TOKEN") or "").strip()

RAW_URLS = [
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/VERSION",
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/master/VERSION",  # fallback
]
API_CONTENTS_URLS = [
    f"https://api.github.com/repos/{OWNER}/{REPO}/contents/VERSION?ref={BRANCH}",
    "https://api.github.com/repos/{OWNER}/{REPO}/contents/VERSION?ref=master",
]

def get_local_version() -> str:
    try:
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def _headers():
    h = {"User-Agent": "lana-modas-updater"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

def get_remote_version(timeout=10) -> str | None:
    # 1) tenta URLs raw (repo público OU privado se tiver token)
    for url in RAW_URLS:
        try:
            r = requests.get(url, timeout=timeout, headers=_headers())
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
        except Exception:
            pass

    # 2) tenta API contents (necessário token se repo for privado)
    for api in API_CONTENTS_URLS:
        try:
            r = requests.get(api, timeout=timeout, headers=_headers())
            if r.status_code == 200:
                data = r.json()
                # quando vem pela API, o arquivo vem em base64
                if isinstance(data, dict) and "content" in data:
                    content = base64.b64decode(data["content"]).decode("utf-8").strip()
                    if content:
                        return content
        except Exception:
            pass

    return None

if __name__ == "__main__":
    local = get_local_version()
    remote = get_remote_version()
    print("Versão local :", local)
    print("Versão remota:", remote)
