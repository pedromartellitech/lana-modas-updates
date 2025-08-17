import os
import requests

# Caminho da versão local
LOCAL_VERSION_FILE = "VERSION"

# URL bruta do arquivo VERSION no GitHub
# ⚠️ depois vamos trocar "SEU_REPOSITORIO" pelo nome correto
REMOTE_VERSION_URL = "https://github.com/pedromartellitech/lana-modas-updates"


def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    return "0.0.0"


def get_remote_version():
    try:
        response = requests.get(REMOTE_VERSION_URL, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print("Erro ao verificar versão remota:", e)
    return None


if __name__ == "__main__":
    local = get_local_version()
    remote = get_remote_version()

    print("Versão local:", local)
    print("Versão remota:", remote)
