"""Encryption utilities for sensitive data."""

import os
import platform
from cryptography.fernet import Fernet
import hashlib


def _generate_machine_key() -> bytes:
    """Generate a machine-specific encryption key.
    
    Creates a deterministic key based on machine-specific information.
    This ensures the same key is generated on the same machine.
    
    Returns:
        bytes: A 32-byte key suitable for Fernet encryption
    """
    # Combine machine-specific identifiers
    machine_id = platform.node() + platform.machine() + platform.system()
    
    # Create a deterministic hash
    key_material = hashlib.sha256(machine_id.encode()).digest()
    
    # Fernet requires a base64-encoded 32-byte key
    return Fernet.generate_key() if not machine_id else \
           Fernet(hashlib.sha256(key_material).digest()[:32] + b'=' * 12)._encryption_key


def get_encryption_key() -> bytes:
    """Get or create the encryption key for this machine.
    
    Returns:
        bytes: Base64-encoded Fernet key
    """
    # Generate a deterministic key based on machine info
    machine_id = platform.node() + platform.machine() + platform.system()
    key_material = hashlib.sha256(machine_id.encode()).digest()
    
    # Fernet requires a URL-safe base64-encoded 32-byte key
    # We'll use the hash directly and encode it properly
    import base64
    key = base64.urlsafe_b64encode(key_material)
    return key


def encrypt_password(password: str) -> str:
    """Encrypt a password using Fernet symmetric encryption.
    
    Args:
        password: Plain text password to encrypt
        
    Returns:
        str: Encrypted password as a base64-encoded string
        
    Raises:
        ValueError: If password is empty
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password using Fernet symmetric encryption.
    
    Args:
        encrypted_password: Encrypted password as a base64-encoded string
        
    Returns:
        str: Decrypted plain text password
        
    Raises:
        ValueError: If encrypted_password is empty
        Exception: If decryption fails (invalid token, wrong key, etc.)
    """
    if not encrypted_password:
        raise ValueError("Encrypted password cannot be empty")
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        raise Exception(f"Failed to decrypt password: {str(e)}")
