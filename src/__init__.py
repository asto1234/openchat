"""
OpenChat - End-to-End Encrypted Chat Application

A production-grade encrypted chat system with:
- E2E encryption (ECDH P-256, AES-256-GCM)
- Persistent message storage (SQLite/PostgreSQL)
- NLP-powered message summarization
- Cloud-native deployment (Docker, Kubernetes)
"""

__version__ = "1.0.0"
__author__ = "OpenChat Team"

# Import core modules for convenience
try:
    from .encryption import SecurityManager
    from .database import DatabaseManager
    from .nlp_summarizer import NLPSummarizer
    from .config import Config
    from .server_interface import CleanServerInterface, ServerConfig
    from .client_architecture import CleanChatClient, ServiceDiscovery
except ImportError:
    pass  # Partial imports allowed during development

__all__ = [
    'SecurityManager',
    'DatabaseManager',
    'NLPSummarizer',
    'Config',
    'CleanServerInterface',
    'ServerConfig',
    'CleanChatClient',
    'ServiceDiscovery',
]
