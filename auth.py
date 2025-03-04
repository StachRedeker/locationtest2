﻿import streamlit as st
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
    Berekent een sleutel via PBKDF2HMAC met de gegeven wachtwoord en salt.
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
    Geeft de SHA-256 hex digest van de inputstring.
    """
    return hashlib.sha256(s.encode()).hexdigest()

def load_users_data():
    """
    Laadt de gebruikersgegevens uit het lokale users.csv-bestand.
    Verwachte kolommen: username_hash, password_hash, salt, enc_config.
    """
    try:
        df = pd.read_csv("users.csv")
        return df
    except Exception as e:
        st.error("Gebruikersgegevens niet beschikbaar: " + str(e))
        return pd.DataFrame()

def authenticate():
    """
    Verifieert een gebruiker door de ingevoerde gebruikersnaam en wachtwoord te hashen en te vergelijken.
    Indien correct, wordt de per-gebruiker globale configuratie (bevat MASTER_PASSWORD en APP_SECRET) ontcijferd
    met een sleutel afgeleid van de concatenatie van gebruikersnaam en wachtwoord (met de opgeslagen salt).
    De ontcijferde configuratie wordt opgeslagen in st.session_state.config.
    """
    df = load_users_data()
    if df.empty:
        st.error("Gebruikersgegevens niet beschikbaar.")
        return None, False

    username = st.text_input("Voer gebruikersnaam in:")
    password = st.text_input("Voer wachtwoord in:", type="password")
    if not username or not password:
        return None, False

    username_hash = hash_str(username)
    password_hash = hash_str(password)

    user_row = df[(df["username_hash"] == username_hash) & (df["password_hash"] == password_hash)]
    if user_row.empty:
        st.error("Onjuiste gebruikersnaam of wachtwoord.")
        return None, False

    salt_str = user_row["salt"].iloc[0]
    enc_config = user_row["enc_config"].iloc[0]
    try:
        salt_bytes = base64.urlsafe_b64decode(salt_str.encode())
        key = derive_key(username + password, salt_bytes)
        config_str = Fernet(key).decrypt(enc_config.encode()).decode()
        st.session_state.config = json.loads(config_str)
    except Exception as e:
        st.error("Kon gebruikersconfiguratie niet ontsleutelen: " + str(e))
        return None, False

    return username, True
