"""
ACARS Server
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
from loguru import logger

# Local Libraries


load_dotenv()

NETWORKS = [
    "vatsim",
    "ivao",
    "pilotedge",
    "poscon",
    "apoc",
    "sayintentions",
    "offline"
]

def generate_key(key_name:str="master"):
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
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
        cipher_text = self.master_key.encrypt(plain_text.encode())
        return cipher_text

    def decrypt(self, cipher_text:bytes) -> str:
        """Decrypts a string"""
        plain_text = self.master_key.decrypt(cipher_text)
        return plain_text.decode()

    def api_key_generator(self, uid:str, network:str) -> str:
        """
        An API key generator
        Requires the UID and network
        """
        if network in NETWORKS:
            pt_api_key = f"{self.random_generator()}:{network}:{uid}"
            ct_api_key = self.encrypt(pt_api_key)
            return base64.b64encode(ct_api_key).decode()
        raise ValueError(f"'{network}' is an invalid network. Expected one of: [{', '.join(NETWORKS)}]")

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
    REDIRECT_URI = "https://efps.vnpas.uk/oauth/token/"

    def __init__(self) -> None:
        pass

    def authorise(self) -> Tuple[str, str]:
        """
        Authorise a user
        Returns a correctly formatted auth URL to use
        """
        state = secrets.token_hex(32)
        payload = {
            "response_type": "code",
            "client_id": os.environ["VATSIM_OAUTH_CLIENT_ID"],
            "redirect_uri": self.REDIRECT_URI,
            "state": state,
            "prompt": "login"
        }
        response = requests.head(self.OAUTH2_AUTH, params=payload)
        logger.debug(response.url)

        return (response.url, state)

    def get_access_token(self, authorisation_code:str) -> Tuple[int, Dict[str,str]]:
        """Gets an access token"""
        payload = {
            "grant_type": "authorization_code",
            "client_id": os.environ["VATSIM_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["VATSIM_OAUTH_CLIENT_SECRET"],
            "redirect_uri": self.REDIRECT_URI,
            "code": authorisation_code
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        response = requests.post(self.OAUTH2_TOKEN, headers=headers, data=payload)

        return (response.status_code, response.json())

    def get_user_details(self, bearer_token:str) -> Tuple[int, Dict[str, Dict[str,str]]]:
        """Gets the user details"""
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }
        response = requests.get(self.AUTH_USER_DETAILS, headers=headers)

        return (response.status_code, response.json())

v = VatsimAuth()
v.get_access_token("def5020017ff888ebcf7c4627c75aa30ae9ce977fa53f075e98a919bce4b307b8462932e2c49c7db33a82e1c20417747c2a7fe81072a6740ca5417d4b8d8a8a077c62327d426dcd0d8101e5b2695ff2559c8151d5f1ee5e52023097a91e0e0cf744b25c0a34b4ea94ab0f38d4bf6cb0b84776be0862915acf315e1f5a8da3a9b65add967304689167f4d3843f1870a1044f012a2194e20324387deec23c7cba04afd029a1252fced9508dd31a7ea3ace974cb9a744cf4bb23382644b57affa21fdbe9a1af702f6972faebc602f483711185242a034ce0f599eefdc9829109a44d0b6e6c01200e025bc07d176274a078c5741b6a19796eb79b8c19be8b9387948d02c3509220d132f67b99381e0b6ac16f7807f8af3e3fc427fafe0a3be93ed6991221b520ace06f632ffd7f81d5f37dd101e6f2da370e14e32a663070c2efc7d2b49e65512f6bac83590e82a496c576464ae7f3c4dcfffba805693235305c4ee68b02e7a7511f0f1763d4f005a")
