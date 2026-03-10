"""Benchmarks for database and storage operations."""

import tempfile
import pytest
from openchat.storage import DatabaseManager, MessageStore


class TestDatabaseBenchmarks:
    """Benchmark database operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up database for benchmarks."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = DatabaseManager(self.db_path)
        self.db.initialize_database()

    def teardown_method(self):
        """Clean up database after benchmarks."""
        self.db.close()
        import os
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_user_creation(self, benchmark):
        """Benchmark user creation."""
        def create_user():
            return self.db.create_user("user_test", "user@test.com")

        result = benchmark(create_user)
        assert result is not None

    def test_user_retrieval(self, benchmark):
        """Benchmark user retrieval."""
        self.db.create_user("user_retrieve", "retrieve@test.com")

        def get_user():
            return self.db.get_user("user_retrieve")

        result = benchmark(get_user)
        assert result is not None
        assert result["username"] == "user_retrieve"

    def test_bulk_user_creation(self, benchmark):
        """Benchmark bulk user creation."""
        def create_users():
            for i in range(100):
                self.db.create_user(f"user_{i}", f"user{i}@test.com")

        benchmark(create_users)
        users = self.db.list_users()
        assert len(users) >= 100

    def test_message_insertion(self, benchmark):
        """Benchmark message insertion."""
        sender = self.db.create_user("sender", "sender@test.com")
        recipient = self.db.create_user("recipient", "recipient@test.com")

        def insert_message():
            return self.db.store_message(
                sender["id"],
                recipient["id"],
                "Test message",
                encrypted=False,
                nonce=b"test_nonce"
            )

        result = benchmark(insert_message)
        assert result is not None

    def test_message_retrieval(self, benchmark):
        """Benchmark message retrieval."""
        sender = self.db.create_user("sender_r", "sender_r@test.com")
        recipient = self.db.create_user("recipient_r", "recipient_r@test.com")
        
        for i in range(10):
            self.db.store_message(
                sender["id"],
                recipient["id"],
                f"Message {i}",
                encrypted=False,
                nonce=f"nonce_{i}".encode()
            )

        def get_messages():
            return self.db.get_conversation(sender["id"], recipient["id"])

        result = benchmark(get_messages)
        assert len(result) >= 10

    def test_bulk_message_insertion(self, benchmark):
        """Benchmark bulk message insertion."""
        sender = self.db.create_user("bulk_sender", "bulk_sender@test.com")
        recipient = self.db.create_user("bulk_recipient", "bulk_recipient@test.com")

        def insert_bulk():
            for i in range(100):
                self.db.store_message(
                    sender["id"],
                    recipient["id"],
                    f"Message {i}",
                    encrypted=False,
                    nonce=f"nonce_{i}".encode()
                )

        benchmark(insert_bulk)
        messages = self.db.get_conversation(sender["id"], recipient["id"])
        assert len(messages) >= 100

    def test_transaction_performance(self, benchmark):
        """Benchmark transaction handling."""
        def transaction():
            with self.db.transaction():
                for i in range(10):
                    self.db.create_user(f"tx_user_{i}", f"tx{i}@test.com")

        benchmark(transaction)

    @pytest.mark.parametrize("num_messages", [10, 50, 100])
    def test_query_performance_different_sizes(self, benchmark, num_messages):
        """Benchmark queries with different result sizes."""
        sender = self.db.create_user(f"sender_{num_messages}", f"sender{num_messages}@test.com")
        recipient = self.db.create_user(f"recip_{num_messages}", f"recip{num_messages}@test.com")

        for i in range(num_messages):
            self.db.store_message(
                sender["id"],
                recipient["id"],
                f"Message {i}",
                encrypted=False,
                nonce=f"nonce_{i}".encode()
            )

        def query():
            return self.db.get_conversation(sender["id"], recipient["id"])

        result = benchmark(query)
        assert len(result) >= num_messages


class TestMessageStoreBenchmarks:
    """Benchmark message store operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up message store for benchmarks."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = DatabaseManager(self.db_path)
        self.db.initialize_database()
        self.store = MessageStore(self.db)

    def teardown_method(self):
        """Clean up after benchmarks."""
        self.db.close()
        import os
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_store_message_performance(self, benchmark):
        """Benchmark message storage."""
        sender = self.db.create_user("msg_sender", "msg_sender@test.com")
        recipient = self.db.create_user("msg_recip", "msg_recip@test.com")

        def store():
            return self.store.store_message(
                sender["id"],
                recipient["id"],
                "Test message content",
                encrypted=True,
                nonce=b"test_nonce"
            )

        result = benchmark(store)
        assert result is not None

    def test_retrieve_messages_performance(self, benchmark):
        """Benchmark message retrieval."""
        sender = self.db.create_user("retrieve_sender", "retrieve_sender@test.com")
        recipient = self.db.create_user("retrieve_recip", "retrieve_recip@test.com")

        for i in range(50):
            self.store.store_message(
                sender["id"],
                recipient["id"],
                f"Message {i}",
                encrypted=True,
                nonce=f"nonce_{i}".encode()
            )

        def retrieve():
            return self.store.get_messages(sender["id"], recipient["id"], limit=50)

        result = benchmark(retrieve)
        assert len(result) >= 50

    def test_search_messages_performance(self, benchmark):
        """Benchmark message search."""
        sender = self.db.create_user("search_sender", "search_sender@test.com")
        recipient = self.db.create_user("search_recip", "search_recip@test.com")

        for i in range(100):
            content = "important" if i % 10 == 0 else f"message {i}"
            self.store.store_message(
                sender["id"],
                recipient["id"],
                content,
                encrypted=False,
                nonce=f"nonce_{i}".encode()
            )

        def search():
            return self.store.search_messages(sender["id"], keyword="important")

        result = benchmark(search)
        assert len(result) >= 10
