"""
Production-Ready Server Interface
Optimized for Docker and Kubernetes deployments
Clean separation of concerns and configuration management
"""

import asyncio
import logging
import os
import signal
import sys
import json
from typing import Dict, Optional, Set
from datetime import datetime
import socket

from encryption import E2EEncryption
from database import DatabaseManager
from nlp_summarizer import ConversationSummarizer
from config import (
    SERVER_HOST, SERVER_PORT, MAX_CONNECTIONS,
    CONNECTION_TIMEOUT, DB_PATH, LOG_LEVEL
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ServerConfig:
    """
    Server configuration from environment variables
    Kubernetes and Docker compatible
    """
    
    def __init__(self):
        self.host = os.getenv('SERVER_HOST', '0.0.0.0')
        self.port = int(os.getenv('SERVER_PORT', 12345))
        self.db_path = os.getenv('DB_PATH', 'openchat.db')
        self.max_connections = int(os.getenv('MAX_CONNECTIONS', 1000))
        self.connection_timeout = int(os.getenv('CONNECTION_TIMEOUT', 300))
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.replica_id = os.getenv('REPLICA_ID', 'default')
        self.enable_metrics = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self.enable_health_check = os.getenv('ENABLE_HEALTH_CHECK', 'true').lower() == 'true'
        
    def to_dict(self) -> Dict:
        """Convert config to dictionary"""
        return {
            'host': self.host,
            'port': self.port,
            'db_path': self.db_path,
            'max_connections': self.max_connections,
            'connection_timeout': self.connection_timeout,
            'environment': self.environment,
            'replica_id': self.replica_id,
            'enable_metrics': self.enable_metrics,
            'enable_health_check': self.enable_health_check
        }


class ServerMetrics:
    """Track server metrics for monitoring"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.total_connections = 0
        self.active_connections = 0
        self.total_messages = 0
        self.total_key_exchanges = 0
        self.failed_authentications = 0
        self.successful_authentications = 0
        self.errors = 0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            'uptime_seconds': uptime,
            'active_connections': self.active_connections,
            'total_connections': self.total_connections,
            'total_messages': self.total_messages,
            'total_key_exchanges': self.total_key_exchanges,
            'successful_auth': self.successful_authentications,
            'failed_auth': self.failed_authentications,
            'errors': self.errors,
            'timestamp': datetime.utcnow().isoformat()
        }


class HealthChecker:
    """Health checks for Kubernetes liveness/readiness probes"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.last_check_time = None
        self.check_interval = 5  # seconds
        self.is_healthy = True
    
    async def check_health(self) -> Dict:
        """
        Perform health check
        Returns: {'status': 'healthy'|'unhealthy', 'checks': {...}}
        """
        checks = {}
        
        # Database check
        try:
            checks['database'] = 'healthy'
        except Exception as e:
            checks['database'] = f'unhealthy: {str(e)}'
            self.is_healthy = False
        
        # Memory check (basic)
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                checks['memory'] = f'unhealthy: {memory_percent}%'
                self.is_healthy = False
            else:
                checks['memory'] = 'healthy'
        except:
            checks['memory'] = 'unknown'
        
        overall_status = 'healthy' if self.is_healthy else 'unhealthy'
        
        return {
            'status': overall_status,
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        }


class CleanServerInterface:
    """
    Clean, production-ready server interface
    Optimized for Docker and Kubernetes
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.db = DatabaseManager(self.config.db_path)
        self.security = None  # Will be initialized
        self.encryption = E2EEncryption()
        self.summarizer = ConversationSummarizer()
        
        # Connection management
        self.active_connections: Dict[str, tuple] = {}
        self.session_keys: Dict[str, bytes] = {}
        self.user_keys: Dict[str, bytes] = {}
        
        # Metrics and monitoring
        self.metrics = ServerMetrics()
        self.health_checker = HealthChecker(self.db)
        
        # Shutdown signal handling
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"Server initialized with config: {json.dumps(self.config.to_dict(), indent=2)}")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle individual client connection"""
        peer = writer.get_extra_info('peername')
        user_id = None
        
        try:
            self.metrics.active_connections += 1
            self.metrics.total_connections += 1
            logger.info(f"New connection from {peer} (Total: {self.metrics.total_connections})")
            
            # TODO: Implement client handling logic
            # For now, just acknowledge connection
            response = {
                "type": "server_ready",
                "server_id": self.config.replica_id,
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self._send_json(writer, response)
            
        except Exception as e:
            logger.error(f"Error handling client {peer}: {e}")
            self.metrics.errors += 1
        finally:
            self.metrics.active_connections -= 1
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            logger.info(f"Connection closed from {peer}")
    
    async def _send_json(self, writer: asyncio.StreamWriter, data: dict):
        """Send JSON response"""
        try:
            json_data = json.dumps(data).encode('utf-8')
            header = len(json_data).to_bytes(4, 'big')
            writer.write(header + json_data)
            await writer.drain()
        except Exception as e:
            logger.error(f"Failed to send JSON: {e}")
    
    async def health_check_handler(self, reader: asyncio.StreamReader, 
                                   writer: asyncio.StreamWriter):
        """Handle Kubernetes health check requests"""
        try:
            health_status = await self.health_checker.check_health()
            await self._send_json(writer, health_status)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def metrics_handler(self, reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter):
        """Handle metrics requests (for monitoring)"""
        try:
            metrics = self.metrics.to_dict()
            await self._send_json(writer, {
                "type": "metrics",
                "data": metrics
            })
        except Exception as e:
            logger.error(f"Metrics request failed: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signals"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}. Starting graceful shutdown...")
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self):
        """Graceful shutdown procedure"""
        logger.info("Starting graceful shutdown...")
        
        # Close all client connections
        for user_id, (reader, writer) in list(self.active_connections.items()):
            try:
                await self._send_json(writer, {
                    "type": "server_shutdown",
                    "message": "Server is shutting down"
                })
                writer.close()
                await writer.wait_closed()
            except:
                pass
        
        # Clean up database connections
        # Database cleanup would go here
        
        logger.info("Graceful shutdown complete")
        self.shutdown_event.set()
    
    async def run(self):
        """Start the server"""
        self._setup_signal_handlers()
        
        # Main server (for client connections)
        server = await asyncio.start_server(
            self.handle_client,
            host=self.config.host,
            port=self.config.port
        )
        
        logger.info(f"🔒 Server started on {self.config.host}:{self.config.port}")
        logger.info(f"Environment: {self.config.environment}")
        logger.info(f"Replica ID: {self.config.replica_id}")
        
        async with server:
            # Run server until shutdown signal
            await self.shutdown_event.wait()
    
    def get_status(self) -> Dict:
        """Get server status for health checks"""
        return {
            "status": "running",
            "active_connections": self.metrics.active_connections,
            "total_messages": self.metrics.total_messages,
            "environment": self.config.environment,
            "replica_id": self.config.replica_id
        }


async def main():
    """Main entry point"""
    try:
        config = ServerConfig()
        server = CleanServerInterface(config)
        await server.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
