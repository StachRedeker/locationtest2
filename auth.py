import streamlit as st
import pandas as pd
import json
import base64
import hashlib
from io import StringIO
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives a Fernet key from the provided password and salt using PBKDF2HMAC.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def hash_str(s: str) -> str:
    """
    Returns the SHA-256 hex digest of the input string.
    """
    return hashlib.sha256(s.encode()).hexdigest()

def load_users_data():
    """
    Loads the users data from the local users.csv file.
    Expected columns: username_hash, password_hash, salt, enc_config.
    """
    try:
        df = pd.read_csv("users.csv")
        return df
    except Exception as e:
        st.error("Users data not available: " + str(e))
        return pd.DataFrame()

def authenticate():
    """
    Authenticates a user by:
      1. Hashing the supplied username and password.
      2. Finding a record with matching username_hash and password_hash.
      3. Using the stored salt (decoded from base64) to derive a key from the concatenation
         of the username and password.
      4. Decrypting the user's enc_config (a JSON string containing global secrets).
         The decrypted config is stored in st.session_state.config.
    """
    df = load_users_data()
    if df.empty:
        st.error("Users data not available.")
        return None, False

    username = st.text_input("Enter username:")
    password = st.text_input("Enter password:", type="password")
    if not username or not password:
        return None, False

    username_hash = hash_str(username)
    password_hash = hash_str(password)

    user_row = df[(df["username_hash"] == username_hash) & (df["password_hash"] == password_hash)]
    if user_row.empty:
        st.error("Incorrect username or password.")
        return None, False

    salt_str = user_row["salt"].iloc[0]
    enc_config = user_row["enc_config"].iloc[0]
    try:
        # Decode the salt (stored as base64) and derive the key from username+password.
        salt_bytes = base64.urlsafe_b64decode(salt_str.encode())
        key = derive_key(username + password, salt_bytes)
        config_str = Fernet(key).decrypt(enc_config.encode()).decode()
        st.session_state.config = json.loads(config_str)
    except Exception as e:
        st.error("Failed to decrypt user configuration: " + str(e))
        return None, False

    return username, True
