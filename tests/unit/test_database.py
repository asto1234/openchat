"""
Test suite for database module
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add openchat package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openchat.storage import DatabaseManager
from openchat.crypto import E2EEncryption


class TestDatabaseManager:
    """Test database operations"""
    
    def setup_method(self):
        """Setup for each test"""
        # Use in-memory database for tests
        self.db = DatabaseManager(":memory:")
        self.enc = E2EEncryption()
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Should not raise any exceptions
        assert self.db is not None
    
    def test_add_user(self):
        """Test adding user"""
        user_id = "user_123"
        username = "alice"
        password_hash = "hash_value"
        password_salt = "salt_value"
        public_key = "-----BEGIN PUBLIC KEY-----\nMFkwEwYH..."
        
        result = self.db.add_user(user_id, username, password_hash, password_salt, public_key)
        assert result is True
    
    def test_get_user(self):
        """Test retrieving user"""
        user_id = "user_123"
        username = "alice"
        password_hash = "hash_value"
        password_salt = "salt_value"
        public_key = "-----BEGIN PUBLIC KEY-----\nMFkwEwYH..."
        
        self.db.add_user(user_id, username, password_hash, password_salt, public_key)
        user = self.db.get_user(username)
        
        assert user is not None
        assert user['username'] == username
        assert user['user_id'] == user_id
    
    def test_get_nonexistent_user(self):
        """Test retrieving nonexistent user"""
        user = self.db.get_user("nonexistent")
        assert user is None
    
    def test_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        user_id1 = "user_1"
        user_id2 = "user_2"
        username = "alice"
        password_hash = "hash"
        password_salt = "salt"
        public_key = "key"
        
        result1 = self.db.add_user(user_id1, username, password_hash, password_salt, public_key)
        result2 = self.db.add_user(user_id2, username, password_hash, password_salt, public_key)
        
        assert result1 is True
        assert result2 is False  # Should fail due to unique constraint
    
    def test_create_conversation(self):
        """Test creating conversation"""
        # Add users
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        self.db.add_user("user_2", "bob", "hash", "salt", "key2")
        
        # Create conversation
        conversation_id = "conv_123"
        result = self.db.create_conversation(conversation_id, "user_1", "user_2")
        
        assert result is True
    
    def test_get_conversation(self):
        """Test retrieving conversation"""
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        self.db.add_user("user_2", "bob", "hash", "salt", "key2")
        
        conversation_id = "conv_123"
        self.db.create_conversation(conversation_id, "user_1", "user_2")
        
        # Should find conversation
        result = self.db.get_conversation("user_1", "user_2")
        assert result == conversation_id
        
        # Should also find in reverse order
        result = self.db.get_conversation("user_2", "user_1")
        assert result == conversation_id
    
    def test_add_message(self):
        """Test adding message"""
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        self.db.add_user("user_2", "bob", "hash", "salt", "key2")
        
        conversation_id = "conv_123"
        self.db.create_conversation(conversation_id, "user_1", "user_2")
        
        message_id = "msg_1"
        encrypted_content = "encrypted_data"
        
        result = self.db.add_message(message_id, conversation_id, "user_1", encrypted_content)
        assert result is True
    
    def test_get_encrypted_messages(self):
        """Test retrieving encrypted messages"""
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        self.db.add_user("user_2", "bob", "hash", "salt", "key2")
        
        conversation_id = "conv_123"
        self.db.create_conversation(conversation_id, "user_1", "user_2")
        
        # Add messages
        for i in range(3):
            self.db.add_message(f"msg_{i}", conversation_id, "user_1", f"encrypted_{i}")
        
        messages = self.db.get_encrypted_messages(conversation_id)
        assert len(messages) == 3
        assert all('encrypted_content' in msg for msg in messages)
    
    def test_save_and_get_session_summary(self):
        """Test saving and retrieving session summary"""
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        self.db.add_user("user_2", "bob", "hash", "salt", "key2")
        
        conversation_id = "conv_123"
        self.db.create_conversation(conversation_id, "user_1", "user_2")
        
        summary_id = "summary_1"
        summary_text = "This is a summary"
        topics = ["tech", "work"]
        message_count = 10
        
        result = self.db.save_session_summary(
            summary_id, conversation_id, "user_1",
            summary_text, topics, message_count
        )
        assert result is True
        
        # Retrieve summary
        summary = self.db.get_session_summary(conversation_id, "user_1")
        assert summary is not None
        assert summary['summary_text'] == summary_text
        assert summary['message_count'] == message_count
        assert summary['topics'] == topics
    
    def test_log_activity(self):
        """Test activity logging"""
        self.db.add_user("user_1", "alice", "hash", "salt", "key1")
        
        self.db.log_activity("user_1", "login")
        self.db.log_activity("user_1", "send_message")
        
        logs = self.db.get_activity_logs("user_1")
        assert len(logs) >= 2
        assert any(log['action'] == 'login' for log in logs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
