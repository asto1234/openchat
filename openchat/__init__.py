"""
OpenChat - Production-Grade End-to-End Encrypted Chat Application

A comprehensive chat system with military-grade encryption, persistent storage,
and NLP-powered message summarization, designed for production deployment on
Kubernetes and Docker.
"""

__version__ = "1.0.0"
__author__ = "OpenChat Team"
__email__ = "team@openchat.dev"
__license__ = "MIT"

# Version info
VERSION = (1, 0, 0)

# Import main components with graceful fallbacks
from openchat.crypto import E2EEncryption, MessageEncryption
from openchat.storage import DatabaseManager

try:
    from openchat.nlp import ConversationSummarizer, DialogueSummarizer
except ImportError:
    ConversationSummarizer = None
    DialogueSummarizer = None

try:
    from openchat.core import Config
except ImportError:
    Config = None

try:
    from openchat.server import CleanServerInterface
except ImportError:
    CleanServerInterface = None

try:
    from openchat.client import CleanChatClient
except ImportError:
    CleanChatClient = None

__all__ = [
    "E2EEncryption",
    "MessageEncryption",
    "DatabaseManager",
    "ConversationSummarizer",
    "DialogueSummarizer",
    "Config",
    "CleanServerInterface",
    "CleanChatClient",
]
