# AES-256-GCM
import os
import secrets
import logging
import datetime
from dataclasses import dataclass
import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)

@dataclass
class EncryptedBundle:
    ciphertext: str
    nonce: str
    salt: str
    auth_tag: str
    algorithm: str
    encrypted_at: str
    key_version: int


