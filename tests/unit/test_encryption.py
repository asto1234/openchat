"""
Test suite for encryption module
"""

import pytest
import sys
from pathlib import Path

# Add openchat package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openchat.crypto import E2EEncryption, MessageEncryption


class TestE2EEncryption:
    """Test end-to-end encryption"""
    
    def setup_method(self):
        """Setup for each test"""
        self.enc = E2EEncryption()
    
    def test_keypair_generation(self):
        """Test ECDH keypair generation"""
        private_key, public_key = self.enc.generate_keypair()
        assert isinstance(private_key, bytes)
        assert isinstance(public_key, bytes)
        assert b"BEGIN PRIVATE KEY" in private_key
        assert b"BEGIN PUBLIC KEY" in public_key
    
    def test_shared_secret_derivation(self):
        """Test ECDH shared secret derivation"""
        # Generate keypairs for two users
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        
        # Derive shared secrets
        secret_a = self.enc.derive_shared_secret(priv_a, pub_b)
        secret_b = self.enc.derive_shared_secret(priv_b, pub_a)
        
        # Shared secrets should match
        assert secret_a == secret_b
        assert len(secret_a) == 32  # 256-bit key
    
    def test_message_encryption_decryption(self):
        """Test AES-256-GCM encryption and decryption"""
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        
        key = self.enc.derive_shared_secret(priv_a, pub_b)
        
        message = "Hello, secret world!"
        encrypted = self.enc.encrypt_message(key, message)
        decrypted = self.enc.decrypt_message(key, encrypted)
        
        assert decrypted == message
        assert encrypted != message  # Should be encrypted
    
    def test_encryption_produces_different_ciphertexts(self):
        """Test that same message produces different ciphertexts (due to random nonce)"""
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        
        key = self.enc.derive_shared_secret(priv_a, pub_b)
        message = "Same message"
        
        encrypted1 = self.enc.encrypt_message(key, message)
        encrypted2 = self.enc.encrypt_message(key, message)
        
        assert encrypted1 != encrypted2  # Different nonces
        assert self.enc.decrypt_message(key, encrypted1) == message
        assert self.enc.decrypt_message(key, encrypted2) == message
    
    def test_decryption_with_wrong_key(self):
        """Test that decryption fails with wrong key"""
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        priv_c, pub_c = self.enc.generate_keypair()
        
        key_ab = self.enc.derive_shared_secret(priv_a, pub_b)
        key_ac = self.enc.derive_shared_secret(priv_a, pub_c)
        
        message = "Secret message"
        encrypted = self.enc.encrypt_message(key_ab, message)
        
        # Try to decrypt with wrong key
        decrypted = self.enc.decrypt_message(key_ac, encrypted)
        assert decrypted is None or decrypted != message
    
    def test_password_hashing(self):
        """Test password hashing"""
        password = "SecurePassword123!"
        
        hash1, salt1 = self.enc.hash_password(password)
        hash2, salt2 = self.enc.hash_password(password)
        
        # Different salts should produce different hashes
        assert hash1 != hash2
        assert salt1 != salt2
        
        # Verify correct password
        assert self.enc.verify_password(password, hash1, salt1)
        assert self.enc.verify_password(password, hash2, salt2)
        
        # Reject wrong password
        assert not self.enc.verify_password("WrongPassword", hash1, salt1)
    
    def test_large_message_encryption(self):
        """Test encryption of large messages"""
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        
        key = self.enc.derive_shared_secret(priv_a, pub_b)
        
        # Create 1MB message
        large_message = "x" * (1024 * 1024)
        encrypted = self.enc.encrypt_message(key, large_message)
        decrypted = self.enc.decrypt_message(key, encrypted)
        
        assert decrypted == large_message
    
    def test_special_characters_in_message(self):
        """Test encryption of messages with special characters"""
        priv_a, pub_a = self.enc.generate_keypair()
        priv_b, pub_b = self.enc.generate_keypair()
        
        key = self.enc.derive_shared_secret(priv_a, pub_b)
        
        message = "Special chars: 你好世界 🔐 !@#$%^&*() \n\t"
        encrypted = self.enc.encrypt_message(key, message)
        decrypted = self.enc.decrypt_message(key, encrypted)
        
        assert decrypted == message


class TestMessageEncryption:
    """Test message encryption wrapper"""
    
    def setup_method(self):
        """Setup for each test"""
        self.msg_enc = MessageEncryption()
    
    def test_session_key_creation(self):
        """Test session key creation"""
        priv_a, pub_a = self.msg_enc.e2e.generate_keypair()
        priv_b, pub_b = self.msg_enc.e2e.generate_keypair()
        
        session_key = self.msg_enc.create_session_key(priv_a, pub_b)
        
        assert isinstance(session_key, bytes)
        assert len(session_key) == 32
    
    def test_encrypt_for_storage(self):
        """Test message encryption for storage"""
        priv_a, pub_a = self.msg_enc.e2e.generate_keypair()
        priv_b, pub_b = self.msg_enc.e2e.generate_keypair()
        
        key = self.msg_enc.create_session_key(priv_a, pub_b)
        message = "Message for storage"
        
        encrypted = self.msg_enc.encrypt_for_storage(message, key)
        decrypted = self.msg_enc.decrypt_from_storage(encrypted, key)
        
        assert decrypted == message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
