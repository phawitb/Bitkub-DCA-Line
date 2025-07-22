# crypto_utils.py
from cryptography.fernet import Fernet
import os

KEY_FILE = "fernet.key"

# Load or generate key
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

fernet = load_key()

def encrypt(value: str) -> str:
    if not value:
        return ""
    return fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    if not value:
        return ""
    return fernet.decrypt(value.encode()).decode()
