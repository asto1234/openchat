"""
Clean Client Architecture for OpenChat
Supports direct connections and service discovery
"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionMode(Enum):
    """Connection modes for client"""
    DIRECT = "direct"           # Direct IP:port connection
    DNS_DISCOVERY = "dns"       # Kubernetes DNS service discovery
    SERVICE_MESH = "service_mesh"  # Service mesh (Istio, Linkerd)


@dataclass
class ServerEndpoint:
    """Server endpoint configuration"""
    host: str
    port: int
    name: str = "default"
    weight: int = 100  # For load balancing
    healthy: bool = True


class ServiceDiscovery:
    """
    Service discovery for finding servers
    Supports Kubernetes service discovery
    """
    
    def __init__(self, mode: ConnectionMode = ConnectionMode.DIRECT):
        self.mode = mode
        self.endpoints: List[ServerEndpoint] = []
        self.current_endpoint_index = 0
    
    @staticmethod
    def from_kubernetes_env() -> 'ServiceDiscovery':
        """Create service discovery from Kubernetes environment"""
        discovery = ServiceDiscovery(ConnectionMode.DNS_DISCOVERY)
        
        # In Kubernetes, service is available at: service-name.namespace.svc.cluster.local
        service_host = os.getenv('OPENCHAT_SERVICE_HOST', 'localhost')
        service_port = int(os.getenv('OPENCHAT_SERVICE_PORT', 12345))
        
        discovery.add_endpoint(ServerEndpoint(
            host=service_host,
            port=service_port,
            name="kubernetes-service"
        ))
        
        return discovery
    
    @staticmethod
    def from_direct_config(host: str, port: int) -> 'ServiceDiscovery':
        """Create service discovery with direct endpoint"""
        discovery = ServiceDiscovery(ConnectionMode.DIRECT)
        discovery.add_endpoint(ServerEndpoint(host=host, port=port))
        return discovery
    
    def add_endpoint(self, endpoint: ServerEndpoint):
        """Add server endpoint"""
        self.endpoints.append(endpoint)
    
    def get_next_endpoint(self) -> Optional[ServerEndpoint]:
        """Get next healthy endpoint (round-robin)"""
        healthy_endpoints = [e for e in self.endpoints if e.healthy]
        
        if not healthy_endpoints:
            logger.warning("No healthy endpoints available")
            return self.endpoints[0] if self.endpoints else None
        
        endpoint = healthy_endpoints[self.current_endpoint_index % len(healthy_endpoints)]
        self.current_endpoint_index += 1
        return endpoint
    
    def mark_endpoint_healthy(self, endpoint: ServerEndpoint):
        """Mark endpoint as healthy"""
        if endpoint in self.endpoints:
            endpoint.healthy = True
    
    def mark_endpoint_unhealthy(self, endpoint: ServerEndpoint):
        """Mark endpoint as unhealthy"""
        if endpoint in self.endpoints:
            endpoint.healthy = False


class ClientConnection:
    """
    Clean client connection handler
    Manages connection lifecycle
    """
    
    def __init__(self, discovery: ServiceDiscovery):
        self.discovery = discovery
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.current_endpoint: Optional[ServerEndpoint] = None
        self.is_connected = False
    
    async def connect(self, retries: int = 3) -> bool:
        """
        Connect to server with retry logic
        
        Args:
            retries: Number of connection attempts
        
        Returns:
            True if connected successfully
        """
        for attempt in range(retries):
            try:
                endpoint = self.discovery.get_next_endpoint()
                if not endpoint:
                    logger.error("No endpoints available")
                    return False
                
                logger.info(f"Connecting to {endpoint.host}:{endpoint.port} (attempt {attempt+1}/{retries})")
                
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(endpoint.host, endpoint.port),
                    timeout=10.0
                )
                
                self.current_endpoint = endpoint
                self.is_connected = True
                logger.info(f"✓ Connected to {endpoint.host}:{endpoint.port}")
                
                return True
            
            except asyncio.TimeoutError:
                logger.warning(f"Connection timeout to {endpoint.host}:{endpoint.port}")
                self.discovery.mark_endpoint_unhealthy(endpoint)
            except ConnectionRefusedError:
                logger.warning(f"Connection refused by {endpoint.host}:{endpoint.port}")
                self.discovery.mark_endpoint_unhealthy(endpoint)
            except Exception as e:
                logger.error(f"Connection error: {e}")
                if endpoint:
                    self.discovery.mark_endpoint_unhealthy(endpoint)
            
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Failed to connect after all retries")
        return False
    
    async def send_message(self, message: dict) -> bool:
        """Send message to server"""
        if not self.is_connected:
            logger.error("Not connected to server")
            return False
        
        try:
            data = json.dumps(message).encode('utf-8')
            header = len(data).to_bytes(4, 'big')
            self.writer.write(header + data)
            await self.writer.drain()
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.is_connected = False
            return False
    
    async def receive_message(self) -> Optional[dict]:
        """Receive message from server"""
        if not self.is_connected:
            return None
        
        try:
            header = await self.reader.readexactly(4)
            length = int.from_bytes(header, 'big')
            
            if length == 0:
                return None
            
            data = await self.reader.readexactly(length)
            return json.loads(data.decode('utf-8'))
        except asyncio.IncompleteReadError:
            self.is_connected = False
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            self.is_connected = False
            return None
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
        
        self.is_connected = False
        logger.info("Disconnected from server")


class CleanChatClient:
    """
    Clean client implementation with service discovery
    """
    
    def __init__(self, discovery: ServiceDiscovery):
        self.discovery = discovery
        self.connection = ClientConnection(discovery)
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
    
    @staticmethod
    def from_kubernetes() -> 'CleanChatClient':
        """Create client configured for Kubernetes"""
        discovery = ServiceDiscovery.from_kubernetes_env()
        return CleanChatClient(discovery)
    
    @staticmethod
    def from_direct(host: str = "127.0.0.1", port: int = 12345) -> 'CleanChatClient':
        """Create client with direct connection"""
        discovery = ServiceDiscovery.from_direct_config(host, port)
        return CleanChatClient(discovery)
    
    async def connect(self) -> bool:
        """Connect to server"""
        return await self.connection.connect()
    
    async def send_message(self, message: dict) -> bool:
        """Send message through connection"""
        return await self.connection.send_message(message)
    
    async def receive_message(self) -> Optional[dict]:
        """Receive message from connection"""
        return await self.connection.receive_message()
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with server"""
        await self.send_message({
            "type": "login",
            "username": username,
            "password": password
        })
        
        response = await self.receive_message()
        if response and response.get("type") == "login_success":
            self.user_id = response.get("user_id")
            self.username = username
            logger.info(f"✓ Authenticated as {username}")
            return True
        
        logger.error("Authentication failed")
        return False
    
    async def disconnect(self):
        """Disconnect from server"""
        await self.connection.disconnect()
    
    async def interactive_chat(self):
        """Interactive chat loop"""
        if not self.connection.is_connected:
            if not await self.connect():
                return
        
        try:
            while True:
                # Read input in non-blocking way
                command = await asyncio.to_thread(input, "> ")
                
                if command == "/quit":
                    break
                
                if command.strip():
                    await self.send_message({
                        "type": "message",
                        "content": command
                    })
                
                # Check for incoming messages
                try:
                    msg = await asyncio.wait_for(
                        self.receive_message(),
                        timeout=0.1
                    )
                    if msg:
                        print(f"[Server]: {msg}")
                except asyncio.TimeoutError:
                    pass
        
        except KeyboardInterrupt:
            logger.info("Chat interrupted")
        finally:
            await self.disconnect()


class ClientPool:
    """
    Pool of client connections for load distribution
    Useful for testing and multi-threaded applications
    """
    
    def __init__(self, discovery: ServiceDiscovery, pool_size: int = 5):
        self.discovery = discovery
        self.pool_size = pool_size
        self.connections: List[ClientConnection] = []
        self.current_index = 0
    
    async def initialize(self) -> bool:
        """Initialize connection pool"""
        logger.info(f"Initializing client pool with {self.pool_size} connections")
        
        for i in range(self.pool_size):
            conn = ClientConnection(self.discovery)
            if await conn.connect():
                self.connections.append(conn)
                logger.info(f"Pool connection {i+1}/{self.pool_size} established")
            else:
                logger.warning(f"Failed to establish pool connection {i+1}")
        
        return len(self.connections) > 0
    
    def get_connection(self) -> Optional[ClientConnection]:
        """Get next available connection"""
        if not self.connections:
            return None
        
        conn = self.connections[self.current_index % len(self.connections)]
        self.current_index += 1
        return conn
    
    async def close_all(self):
        """Close all connections in pool"""
        logger.info("Closing client pool")
        for conn in self.connections:
            await conn.disconnect()
        self.connections.clear()


async def main():
    """Example usage"""
    # Example 1: Direct connection
    logger.info("Example 1: Direct connection")
    client = CleanChatClient.from_direct("127.0.0.1", 12345)
    
    if await client.connect():
        await client.send_message({"type": "ping"})
        response = await client.receive_message()
        print(f"Response: {response}")
        await client.disconnect()
    
    # Example 2: Kubernetes service discovery
    logger.info("Example 2: Kubernetes service discovery")
    k8s_client = CleanChatClient.from_kubernetes()
    if await k8s_client.connect():
        print("Connected via Kubernetes service discovery")
        await k8s_client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
