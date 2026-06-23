"""
ACARS Server
Authentication
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import base64
import os
import secrets
import string
from typing import Dict, Tuple

# Third Party Libraries
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from opentelemetry import trace

# Local Libraries
from acars_server import common, static_data


load_dotenv()

def generate_master_key(key_name:str="master"):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(f"{key_name}.key", "wb") as key_file:
        key_file.write(key)

def generate_auth_key(key_name:str="auth"):
    """
    Generates a key and save it into a file
    """
    key = secrets.token_bytes(32)
    with open(f"{key_name}.key", "wb") as key_file:
        key_file.write(key)


class Auth:
    """A class to encrypt and decrypt stuff"""

    def __init__(self) -> None:
        self.master_key = Fernet(self._load_key())

    @staticmethod
    def _load_key(key_name:str="master"):
        """
        Loads the key from the current directory
        """
        return open(f"{key_name}.key", "rb").read()

    @staticmethod
    def random_generator(length:int=32) -> str:
        """Generates a secure random string"""
        alphabet = string.ascii_letters + string.digits
        secure_string = ''.join(secrets.choice(alphabet) for _ in range(length))
        return secure_string

    def encrypt(self, plain_text:str) -> bytes:
        """Encrypts a string"""
        current_span = trace.get_current_span()
        current_span.add_event("Start encryption function")
        cipher_text = self.master_key.encrypt(plain_text.encode())
        current_span.add_event("End encryption function")
        return cipher_text

    def decrypt(self, cipher_text:bytes) -> str:
        """Decrypts a string"""
        current_span = trace.get_current_span()
        current_span.add_event("Start decryption function")
        plain_text = self.master_key.decrypt(cipher_text)
        current_span.add_event("End decryption function")
        return plain_text.decode()

    def api_key_generator(self, uid:str, network:str) -> str:
        """
        An API key generator
        Requires the UID and network
        """
        if network in static_data.NETWORKS:
            current_span = trace.get_current_span()
            pt_api_key = f"{self.random_generator()}:{network}:{uid}"
            ct_api_key = self.encrypt(pt_api_key)
            common.logger.success("API key created")
            current_span.add_event("API Key Created")
            return base64.b64encode(ct_api_key).decode()
        raise ValueError(
            (f"'{network}' is an invalid network. Expected one of: "
            f"[{', '.join(static_data.NETWORKS)}]"))

    def api_key_reader(self, api_key:str) -> Dict[str,str]:
        """Read an API key"""
        pt_api_key = self.decrypt(base64.b64decode(api_key))
        pt_vars = pt_api_key.split(":")

        return {
            "network": pt_vars[1],
            "uid": pt_vars[2]
        }


class VatsimAuth:
    """A Vatsim OAuth2 Class"""

    OAUTH2_AUTH = "https://auth.vatsim.net/oauth/authorize"
    OAUTH2_TOKEN = "https://auth.vatsim.net/oauth/token"
    AUTH_USER_DETAILS = "https://auth.vatsim.net/api/user"

    def __init__(self, redirect_type:str="aircraft") -> None:
        if redirect_type == "aircraft":
            self.redirect_uri = os.getenv("VATSIM_OAUTH_REDIRECT_URI_AIRCRAFT")
        elif redirect_type == "atsu":
            self.redirect_uri = os.getenv("VATSIM_OAUTH_REDIRECT_URI_ATSU")
        else:
            raise ValueError(
                ("Unexpected redirect type. Expected one "
                 f"of aircraft, atsu. Received {redirect_type}"))
        self.redirect_type = redirect_type

    def authorise(self) -> Tuple[str, str]:
        """
        Authorise a user
        Returns a correctly formatted auth URL to use
        """
        state = secrets.token_hex(32)
        payload = {
            "response_type": "code",
            "client_id": os.getenv("VATSIM_OAUTH_CLIENT_ID"),
            "redirect_uri": self.redirect_uri,
            "state": state,
            "prompt": "login"
        }
        # If logging on as an ATSU, we need vatsim details to verify ATC rating
        if self.redirect_type == "atsu":
            payload["scope"] = "vatsim_details"
            payload["prompt"] = "none"
        response = requests.head(self.OAUTH2_AUTH, params=payload, timeout=10)

        return (response.url, state)

    def get_access_token(
            self, authorisation_code:str) -> Tuple[int, Dict[str,str]]: # pragma: no cover
        """Gets an access token"""
        payload = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("VATSIM_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("VATSIM_OAUTH_CLIENT_SECRET"),
            "redirect_uri": self.redirect_uri,
            "code": authorisation_code
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        response = requests.post(self.OAUTH2_TOKEN, headers=headers, data=payload, timeout=10)

        return (response.status_code, response.json())

    def get_user_details(
            self, bearer_token:str) -> Tuple[int, Dict[str, Dict[str,str]]]: # pragma: no cover
        """Gets the user details"""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }
        response = requests.get(self.AUTH_USER_DETAILS, headers=headers, timeout=10)

        return (response.status_code, response.json())
