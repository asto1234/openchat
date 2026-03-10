"""
Database Module for Message Storage
Handles encrypted message storage with SQLite/PostgreSQL
Server cannot read messages - they're encrypted end-to-end
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages encrypted message storage
    Messages are stored encrypted; server only stores ciphertext
    """
    
    def __init__(self, db_path: str = "openchat.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    public_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user1_id TEXT NOT NULL,
                    user2_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user1_id) REFERENCES users(user_id),
                    FOREIGN KEY(user2_id) REFERENCES users(user_id),
                    UNIQUE(user1_id, user2_id)
                )
            ''')
            
            # Messages table - stores ENCRYPTED messages only
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    encrypted_content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(sender_id) REFERENCES users(user_id)
                )
            ''')
            
            # Session summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_summaries (
                    summary_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    topics TEXT,
                    message_count INTEGER,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Activity logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id)')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def add_user(self, user_id: str, username: str, password_hash: str, 
                 password_salt: str, public_key: str) -> bool:
        """Add new user to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, username, password_hash, password_salt, public_key)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, password_hash, password_salt, public_key))
                conn.commit()
                logger.info(f"User created: {username}")
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed: {e}")
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Retrieve user by username"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Retrieve user by user_id"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_public_key(self, user_id: str) -> Optional[str]:
        """Get user's public key for key exchange"""
        user = self.get_user_by_id(user_id)
        return user['public_key'] if user else None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?',
                (user_id,)
            )
            conn.commit()
    
    def create_conversation(self, conversation_id: str, user1_id: str, user2_id: str) -> bool:
        """Create a new conversation between two users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations (conversation_id, user1_id, user2_id)
                    VALUES (?, ?, ?)
                ''', (conversation_id, user1_id, user2_id))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Conversation already exists
            return False
    
    def get_conversation(self, user1_id: str, user2_id: str) -> Optional[str]:
        """Get conversation ID for two users"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT conversation_id FROM conversations 
                WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
            ''', (user1_id, user2_id, user2_id, user1_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_message(self, message_id: str, conversation_id: str, sender_id: str,
                   encrypted_content: str) -> bool:
        """
        Store encrypted message
        NOTE: Only encrypted content is stored - server cannot read messages
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (message_id, conversation_id, sender_id, encrypted_content)
                    VALUES (?, ?, ?, ?)
                ''', (message_id, conversation_id, sender_id, encrypted_content))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return False
    
    def get_encrypted_messages(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve encrypted messages from conversation
        Client will decrypt these with session key
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_id, sender_id, encrypted_content, timestamp 
                FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (conversation_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_session_summary(self, summary_id: str, conversation_id: str, user_id: str,
                            summary_text: str, topics: List[str], message_count: int) -> bool:
        """Store conversation summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                topics_json = json.dumps(topics)
                cursor.execute('''
                    INSERT INTO session_summaries 
                    (summary_id, conversation_id, user_id, summary_text, topics, message_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (summary_id, conversation_id, user_id, summary_text, topics_json, message_count))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            return False
    
    def get_session_summary(self, conversation_id: str, user_id: str) -> Optional[Dict]:
        """Retrieve latest session summary for user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM session_summaries 
                WHERE conversation_id = ? AND user_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
            ''', (conversation_id, user_id))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['topics'] = json.loads(result['topics'])
                return result
            return None
    
    def log_activity(self, user_id: str, action: str):
        """Log user activity for security/audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO activity_logs (user_id, action) VALUES (?, ?)',
                    (user_id, action)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def get_activity_logs(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get user's activity logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM activity_logs 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Test database
    db = DatabaseManager(":memory:")
    print("✓ Database initialized successfully")
