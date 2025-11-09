"""Encryption utilities for sensitive data."""
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import base64
import hashlib

load_dotenv()

class Encryptor:
    """Handle encryption/decryption of sensitive data."""
    
    def __init__(self):
        # Get encryption key from environment
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        # Convert to proper Fernet key format (32 bytes, base64-encoded)
        key_bytes = hashlib.sha256(encryption_key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        
        self.cipher = Fernet(fernet_key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string."""
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a string."""
        if not encrypted_text:
            return ""
        
        decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()

# Global encryptor instance
encryptor = Encryptor()
