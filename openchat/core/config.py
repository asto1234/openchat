"""
Configuration and constants for OpenChat
"""

import os
from pathlib import Path

# Application settings
APP_NAME = "OpenChat"
APP_VERSION = "1.0.0"

# Server settings
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 12345))
MAX_CONNECTIONS = 1000
CONNECTION_TIMEOUT = 300  # seconds

# Database settings
DB_PATH = os.getenv("DB_PATH", "openchat.db")
DB_BACKUP_DIR = os.getenv("DB_BACKUP_DIR", "backups")

# Security settings
MIN_PASSWORD_LENGTH = 8
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 32
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 300  # seconds
ACCOUNT_LOCKOUT_DURATION = 3600  # seconds (1 hour)

# Encryption settings
ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_EXCHANGE_CURVE = "SECP256R1"  # P-256
HASH_ALGORITHM = "SHA256"
PBKDF2_ITERATIONS = 100000

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Message settings
MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MB
MESSAGE_TIMEOUT = 30  # seconds

# NLP settings
NLP_MODEL = "facebook/bart-large-cnn"
NLP_FALLBACK_MODEL = "sshleifer/distilbart-cnn-6-6"
MAX_SUMMARY_LENGTH = 200
MIN_SUMMARY_LENGTH = 50

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "openchat.log"
LOG_MAX_BYTES = 10485760  # 10 MB
LOG_BACKUP_COUNT = 5

# Session settings
SESSION_TIMEOUT = 3600  # seconds (1 hour)
SESSION_KEY_DERIVATION = "HKDF-SHA256"

# Feature flags
ENABLE_MESSAGE_HISTORY = True
ENABLE_SUMMARIZATION = True
ENABLE_ENCRYPTION = True
ENABLE_AUDIT_LOG = True

# Security headers
CORS_ORIGINS = ["*"]  # Restrict in production
SECURE_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
}

# Protocol constants
PROTOCOL_VERSION = "1.0.0"
BUFFER_SIZE = 4096
NONCE_SIZE = 12
KEY_SIZE = 32

# Message types
MESSAGE_TYPES = {
    "auth_required": "Server requests authentication",
    "register": "Client registers new account",
    "login": "Client logs in",
    "registration_success": "Registration successful",
    "login_success": "Login successful",
    "authenticated": "Authentication complete",
    "key_exchange": "ECDH key exchange request",
    "key_exchange_success": "Key exchange successful",
    "send_message": "Send encrypted message",
    "new_message": "Receive encrypted message",
    "get_summary": "Request conversation summary",
    "summary": "Conversation summary response",
    "list_users": "Request user list",
    "user_list": "User list response",
    "disconnect": "Client disconnecting",
    "error": "Error response"
}

# Create necessary directories
Path(DB_BACKUP_DIR).mkdir(exist_ok=True)
