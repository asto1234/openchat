"""
End-to-End Encryption Module
Implements AES-256-GCM for message encryption with ECDH key exchange
Server cannot decrypt messages as it never has access to session keys
"""

import os
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import hashlib
import secrets
from typing import Tuple, Optional, Dict


class E2EEncryption:
    """
    End-to-End Encryption using ECDH + HKDF + AES-256-GCM
    Each user pair has a unique shared secret derived from ECDH
    """
    
    def __init__(self):
        self.backend = default_backend()
        self.key_size = 32  # 256-bit keys
        self.nonce_size = 12  # 96-bit nonce for GCM
        
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate ECDH keypair (P-256 curve)
        Returns: (private_key_bytes, public_key_bytes)
        """
        private_key = ec.generate_private_key(ec.SECP256R1(), self.backend)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem
    
    def derive_shared_secret(self, private_key_pem: bytes, peer_public_key_pem: bytes) -> bytes:
        """
        Derive shared secret using ECDH
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=self.backend
        )
        peer_public_key = serialization.load_pem_public_key(
            peer_public_key_pem, backend=self.backend
        )
        shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
        
        # Use HKDF to derive a 256-bit key from shared secret
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=None,
            info=b'e2e_chat_encryption',
            backend=self.backend
        )
        derived_key = hkdf.derive(shared_secret)
        return derived_key
    
    def encrypt_message(self, key: bytes, plaintext: str) -> str:
        """
        Encrypt message with AES-256-GCM
        Returns: base64-encoded (nonce + ciphertext + tag)
        """
        nonce = secrets.token_bytes(self.nonce_size)
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Combine nonce + ciphertext (ciphertext includes auth tag)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_message(self, key: bytes, encrypted_message: str) -> Optional[str]:
        """
        Decrypt message with AES-256-GCM
        """
        try:
            encrypted_data = base64.b64decode(encrypted_message)
            nonce = encrypted_data[:self.nonce_size]
            ciphertext = encrypted_data[self.nonce_size:]
            
            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash password using PBKDF2 with SHA256
        Returns: (hashed_password_b64, salt_b64)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # 100k iterations for PBKDF2
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return base64.b64encode(key).decode('utf-8'), base64.b64encode(salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify password against hash
        """
        salt_bytes = base64.b64decode(salt)
        computed_hash, _ = self.hash_password(password, salt_bytes)
        return computed_hash == hashed_password


class MessageEncryption:
    """
    Handles message encryption/decryption with session keys
    Server stores encrypted messages but cannot read them
    """
    
    def __init__(self):
        self.e2e = E2EEncryption()
        self.session_keys: Dict[str, bytes] = {}  # Client-side only
    
    def create_session_key(self, private_key_pem: bytes, peer_public_key_pem: bytes) -> bytes:
        """
        Create a session-specific key (client-side)
        """
        return self.e2e.derive_shared_secret(private_key_pem, peer_public_key_pem)
    
    def encrypt_for_storage(self, message: str, key: bytes) -> str:
        """Encrypt message for storage in database"""
        return self.e2e.encrypt_message(key, message)
    
    def decrypt_from_storage(self, encrypted_message: str, key: bytes) -> Optional[str]:
        """Decrypt message retrieved from database"""
        return self.e2e.decrypt_message(key, encrypted_message)


if __name__ == "__main__":
    # Test encryption
    enc = E2EEncryption()
    
    # Generate keypairs for two users
    priv_a, pub_a = enc.generate_keypair()
    priv_b, pub_b = enc.generate_keypair()
    
    # Derive shared secrets
    secret_a = enc.derive_shared_secret(priv_a, pub_b)
    secret_b = enc.derive_shared_secret(priv_b, pub_a)
    
    # Verify they match
    assert secret_a == secret_b, "Shared secrets don't match!"
    
    # Test encryption/decryption
    message = "Hello, secret world!"
    encrypted = enc.encrypt_message(secret_a, message)
    print(f"Encrypted: {encrypted}")
    
    decrypted = enc.decrypt_message(secret_b, encrypted)
    print(f"Decrypted: {decrypted}")
    assert decrypted == message, "Decryption failed!"
    
    print("✓ E2E Encryption tests passed!")
