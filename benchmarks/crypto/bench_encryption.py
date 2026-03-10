"""Benchmarks for cryptographic operations."""

import pytest
from openchat.crypto import E2EEncryption, SecurityManager


class TestEncryptionBenchmarks:
    """Benchmark encryption and decryption operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up encryption for benchmarks."""
        self.security = SecurityManager()
        self.e2e = E2EEncryption(self.security.generate_key_pair())

    def test_key_pair_generation(self, benchmark):
        """Benchmark key pair generation."""
        def generate_keys():
            return self.security.generate_key_pair()

        result = benchmark(generate_keys)
        assert result[0] is not None
        assert result[1] is not None

    def test_key_exchange(self, benchmark):
        """Benchmark ECDH key exchange."""
        remote_pub, remote_priv = self.security.generate_key_pair()

        def exchange_keys():
            return self.security.perform_key_exchange(
                self.e2e.private_key,
                remote_pub
            )

        shared_secret = benchmark(exchange_keys)
        assert shared_secret is not None
        assert len(shared_secret) > 0

    def test_message_encryption(self, benchmark):
        """Benchmark message encryption."""
        message = b"Test message for encryption benchmarking"

        def encrypt_msg():
            return self.e2e.encrypt_message(message)

        encrypted = benchmark(encrypt_msg)
        assert encrypted is not None

    def test_message_decryption(self, benchmark):
        """Benchmark message decryption."""
        message = b"Test message for decryption benchmarking"
        encrypted = self.e2e.encrypt_message(message)

        def decrypt_msg():
            return self.e2e.decrypt_message(encrypted)

        decrypted = benchmark(decrypt_msg)
        assert decrypted == message

    def test_encrypt_decrypt_cycle(self, benchmark):
        """Benchmark full encrypt/decrypt cycle."""
        message = b"Test message for full cycle benchmarking"

        def cycle():
            encrypted = self.e2e.encrypt_message(message)
            return self.e2e.decrypt_message(encrypted)

        result = benchmark(cycle)
        assert result == message

    def test_derive_key(self, benchmark):
        """Benchmark key derivation."""
        password = b"test_password_for_benchmarking"

        def derive():
            return self.security.derive_key(password)

        key = benchmark(derive)
        assert key is not None
        assert len(key) == 32

    @pytest.mark.parametrize("size", [128, 256, 512, 1024, 4096])
    def test_encryption_different_sizes(self, benchmark, size):
        """Benchmark encryption with different message sizes."""
        message = b"x" * size

        def encrypt():
            return self.e2e.encrypt_message(message)

        encrypted = benchmark(encrypt)
        assert encrypted is not None

    def test_concurrent_key_exchanges(self, benchmark):
        """Benchmark concurrent key exchanges."""
        pairs = [self.security.generate_key_pair() for _ in range(10)]

        def exchange():
            results = []
            for pub, priv in pairs:
                result = self.security.perform_key_exchange(
                    self.e2e.private_key,
                    pub
                )
                results.append(result)
            return results

        results = benchmark(exchange)
        assert len(results) == 10
        assert all(r is not None for r in results)


class TestSecurityManagerBenchmarks:
    """Benchmark SecurityManager operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up SecurityManager for benchmarks."""
        self.manager = SecurityManager()

    def test_hash_generation(self, benchmark):
        """Benchmark hash generation."""
        data = b"Test data for hashing" * 100

        def hash_data():
            import hashlib
            return hashlib.sha256(data).hexdigest()

        result = benchmark(hash_data)
        assert result is not None
        assert len(result) == 64

    def test_signature_generation(self, benchmark):
        """Benchmark signature generation."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        data = b"Test data for signature"

        def sign():
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            return private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

        signature = benchmark(sign)
        assert signature is not None
