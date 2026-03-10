#!/usr/bin/env python3
"""
Example: Deploying OpenChat Server with Clean Interface on Docker/Kubernetes

This example demonstrates:
1. Starting the clean server interface (server_interface.py)
2. Integrating with encryption, database, and NLP modules
3. Handling Kubernetes configuration
4. Running health checks and metrics endpoints

Usage:
    # Run locally with environment variables
    SERVER_HOST=0.0.0.0 SERVER_PORT=12345 python example_k8s_deployment.py
    
    # Or in Docker/Kubernetes (vars injected via ConfigMap)
    python example_k8s_deployment.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add openchat package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import clean server interface
from openchat.server import CleanServerInterface, ServerConfig, ServerMetrics

# Import your existing modules
try:
    from openchat.crypto import SecurityManager
    from openchat.storage import DatabaseManager
    from openchat.nlp import ConversationSummarizer
    from openchat.core import Config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure OpenChat package is properly installed")
    sys.exit(1)


class OpenChatServerDeployment:
    """
    Production-ready OpenChat server with all components integrated.
    
    This class demonstrates how to:
    - Initialize server configuration from environment
    - Set up security manager for E2E encryption
    - Initialize database with persistence
    - Integrate NLP summarization
    - Run health checks compatible with Kubernetes
    """
    
    def __init__(self):
        """Initialize all server components."""
        self.logger = self._setup_logging()
        self.logger.info("Initializing OpenChat Server Deployment")
        
        # Load configuration from environment (Kubernetes ConfigMap compatible)
        self.config = ServerConfig()
        self.logger.info(f"Server Config - Host: {self.config.host}, Port: {self.config.port}")
        
        # Initialize security manager for E2E encryption
        self.security = None
        self.database = None
        self.nlp = None
        self.server = None
    
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for container environments."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Create logger
        logger = logging.getLogger('openchat-server')
        logger.setLevel(getattr(logging, log_level))
        
        # Console handler with structured format
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_security(self) -> SecurityManager:
        """
        Initialize end-to-end encryption security manager.
        
        This handles:
        - Key exchange (ECDH P-256)
        - Message encryption (AES-256-GCM)
        - Authentication
        """
        self.logger.info("Initializing Security Manager")
        try:
            security = SecurityManager()
            self.logger.info("Security Manager initialized successfully")
            return security
        except Exception as e:
            self.logger.error(f"Failed to initialize Security Manager: {e}")
            raise
    
    def _initialize_database(self) -> DatabaseManager:
        """
        Initialize database manager with persistent storage.
        
        For Kubernetes:
        - Uses /data/openchat.db from PersistentVolume
        - Automatically creates tables if missing
        - Supports multiple replicas (shared database)
        """
        db_path = self.config.db_path
        self.logger.info(f"Initializing Database at: {db_path}")
        
        try:
            # Ensure parent directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            database = DatabaseManager(db_path)
            database.initialize()
            
            # Get database stats
            tables = database.get_table_info()
            self.logger.info(f"Database initialized with tables: {list(tables.keys())}")
            
            return database
        except Exception as e:
            self.logger.error(f"Failed to initialize Database: {e}")
            raise
    
    def _initialize_nlp(self) -> ConversationSummarizer:
        """
        Initialize NLP summarization for message summaries.
        
        This is optional; failures won't crash the server.
        """
        self.logger.info("Initializing NLP Summarizer")
        try:
            nlp = ConversationSummarizer()
            self.logger.info("NLP Summarizer initialized successfully")
            return nlp
        except Exception as e:
            self.logger.warning(f"NLP Summarizer failed to initialize: {e}")
            self.logger.warning("Server will continue without summarization features")
            return None
    
    def _initialize_server(self) -> CleanServerInterface:
        """Create the clean server interface with all components."""
        self.logger.info("Initializing Clean Server Interface")
        
        server = CleanServerInterface(
            host=self.config.host,
            port=self.config.port,
            db_path=self.config.db_path,
            max_connections=self.config.max_connections,
            security_manager=self.security,
            database_manager=self.database,
            nlp_summarizer=self.nlp
        )
        
        self.logger.info(f"Server Interface ready at {self.config.host}:{self.config.port}")
        return server
    
    async def start(self):
        """Start the complete OpenChat server deployment."""
        try:
            # Initialize all components in order
            self.logger.info("=" * 60)
            self.logger.info("OPENCHAT SERVER STARTUP")
            self.logger.info("=" * 60)
            
            # 1. Security
            self.security = self._initialize_security()
            
            # 2. Database
            self.database = self._initialize_database()
            
            # 3. NLP (optional)
            self.nlp = self._initialize_nlp()
            
            # 4. Server
            self.server = self._initialize_server()
            
            # Log environment info
            self._log_environment_info()
            
            self.logger.info("=" * 60)
            self.logger.info("STARTING SERVER")
            self.logger.info("=" * 60)
            
            # Start the server
            await self.server.run()
            
        except Exception as e:
            self.logger.error(f"FATAL ERROR: {e}", exc_info=True)
            sys.exit(1)
    
    def _log_environment_info(self):
        """Log deployment environment information."""
        replica_id = os.getenv('REPLICA_ID', 'local-dev')
        pod_name = os.getenv('POD_NAME', 'localhost')
        namespace = os.getenv('POD_NAMESPACE', 'default')
        
        self.logger.info(f"Deployment Environment:")
        self.logger.info(f"  Replica ID: {replica_id}")
        self.logger.info(f"  Pod Name: {pod_name}")
        self.logger.info(f"  Namespace: {namespace}")
        self.logger.info(f"  Enable Metrics: {self.config.enable_metrics}")
        self.logger.info(f"  Enable Health Checks: {self.config.enable_health_check}")


def main():
    """Main entry point for the server."""
    deployment = OpenChatServerDeployment()
    
    # Run the async server
    try:
        asyncio.run(deployment.start())
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"Unhandled error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
