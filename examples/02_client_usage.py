#!/usr/bin/env python3
"""
Example: OpenChat Client with Service Discovery and Connection Pooling

This example demonstrates:
1. Service discovery in Kubernetes environment
2. Client connection with retry logic and exponential backoff
3. Interactive chat interface
4. Connection pooling for multiple conversations
5. Graceful error handling

Usage:
    # Local deployment (direct connection)
    python example_client_usage.py
    
    # Kubernetes deployment (automatic service discovery)
    kubectl exec -it openchat-0 -- python example_client_usage.py
    
    # With custom server
    python example_client_usage.py --host localhost --port 12345
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from argparse import ArgumentParser
from typing import Optional

# Add openchat package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import clean client architecture
from openchat.client import (
    ServiceDiscovery,
    CleanChatClient,
    ClientPool,
    ConnectionMode,
    ServerEndpoint
)


class OpenChatClientApp:
    """
    Interactive OpenChat client with service discovery.
    
    Features:
    - Automatic Kubernetes service discovery
    - Connection pooling for multiple chats
    - Retry logic with exponential backoff
    - Interactive command interface
    """
    
    def __init__(self, discovery: ServiceDiscovery):
        """
        Initialize the chat client.
        
        Args:
            discovery: ServiceDiscovery instance for endpoint management
        """
        self.logger = self._setup_logging()
        self.discovery = discovery
        self.client = None
        self.pool = None
        self.authenticated = False
        self.current_user = None
    
    def _setup_logging(self) -> logging.Logger:
        """Configure client-side logging."""
        logger = logging.getLogger('openchat-client')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s [CLIENT] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def connect_to_server(self, username: str, password: str) -> bool:
        """
        Connect to OpenChat server with authentication.
        
        Args:
            username: User login name
            password: User password
            
        Returns:
            True if connection successful, False otherwise
        """
        self.logger.info("Connecting to OpenChat server...")
        
        try:
            # Create client instance
            self.client = CleanChatClient(
                discovery=self.discovery,
                logger=self.logger
            )
            
            # Attempt connection with retries
            endpoint = self.discovery.get_next_endpoint()
            if not endpoint:
                self.logger.error("No server endpoints available")
                return False
            
            self.logger.info(f"Connecting to {endpoint.host}:{endpoint.port}...")
            
            # Connect with timeout
            connected = await asyncio.wait_for(
                self.client.connect(),
                timeout=10.0
            )
            
            if not connected:
                self.logger.error("Failed to connect to server")
                return False
            
            # Authenticate
            self.logger.info(f"Authenticating as {username}...")
            authenticated = await self.client.authenticate(username, password)
            
            if authenticated:
                self.authenticated = True
                self.current_user = username
                self.logger.info(f"Successfully authenticated as {username}")
                
                # Mark endpoint as healthy
                self.discovery.mark_endpoint_healthy(endpoint)
                
                return True
            else:
                self.logger.error("Authentication failed")
                self.discovery.mark_endpoint_unhealthy(endpoint)
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("Connection timeout")
            if endpoint:
                self.discovery.mark_endpoint_unhealthy(endpoint)
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            if endpoint:
                self.discovery.mark_endpoint_unhealthy(endpoint)
            return False
    
    async def send_message(self, recipient: str, message: str) -> bool:
        """
        Send an encrypted message to another user.
        
        Args:
            recipient: Username of recipient
            message: Message content
            
        Returns:
            True if message sent successfully
        """
        if not self.authenticated or not self.client:
            self.logger.error("Not connected or authenticated")
            return False
        
        try:
            self.logger.info(f"Sending message to {recipient}...")
            sent = await self.client.send_message(recipient, message)
            
            if sent:
                self.logger.info(f"Message delivered to {recipient}")
                return True
            else:
                self.logger.error(f"Failed to send message to {recipient}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_messages(self) -> Optional[dict]:
        """
        Receive an incoming message.
        
        Returns:
            Message dict with sender, content, timestamp; None if timeout
        """
        if not self.authenticated or not self.client:
            self.logger.error("Not connected or authenticated")
            return None
        
        try:
            message = await asyncio.wait_for(
                self.client.receive_message(),
                timeout=30.0
            )
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None
    
    async def interactive_chat(self):
        """Run interactive chat interface."""
        if not self.authenticated:
            self.logger.error("Must authenticate first")
            return
        
        print("\n" + "=" * 60)
        print("OpenChat Interactive Session")
        print("=" * 60)
        print(f"User: {self.current_user}")
        print("Commands:")
        print("  /msg <user> <message>  - Send message")
        print("  /listen                - Listen for messages")
        print("  /status                - Show connection status")
        print("  /quit                  - Exit")
        print("=" * 60 + "\n")
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Get user input
                user_input = await loop.run_in_executor(
                    None,
                    input,
                    f"{self.current_user}> "
                )
                
                if not user_input.strip():
                    continue
                
                # Parse command
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                
                if command == '/quit' or command == '/exit':
                    print("Goodbye!")
                    break
                
                elif command == '/msg' and len(parts) > 1:
                    # Format: /msg user message
                    remaining = parts[1].split(maxsplit=1)
                    if len(remaining) < 2:
                        print("Usage: /msg <user> <message>")
                        continue
                    
                    recipient = remaining[0]
                    message = remaining[1]
                    
                    await self.send_message(recipient, message)
                
                elif command == '/listen':
                    print("Listening for messages (30s timeout)...")
                    message = await self.receive_messages()
                    
                    if message:
                        print(f"\n[{message.get('sender')}]: {message.get('content')}")
                    else:
                        print("No messages received (timeout)")
                
                elif command == '/status':
                    print(f"Connected: {self.authenticated}")
                    print(f"User: {self.current_user}")
                    endpoint = self.discovery.get_current_endpoint()
                    if endpoint:
                        print(f"Server: {endpoint.host}:{endpoint.port}")
                    print(f"Total endpoints: {len(self.discovery.endpoints)}")
                
                else:
                    print("Unknown command. Type /quit to exit.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"Chat error: {e}")
    
    async def disconnect(self):
        """Gracefully disconnect from server."""
        if self.client:
            self.logger.info("Disconnecting from server...")
            await self.client.disconnect()
            self.authenticated = False
            self.logger.info("Disconnected")


async def main():
    """Main client application entry point."""
    
    # Parse command-line arguments
    parser = ArgumentParser(description='OpenChat Client')
    parser.add_argument(
        '--host',
        default=os.getenv('SERVER_HOST', 'localhost'),
        help='Server host (default: localhost or env SERVER_HOST)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('SERVER_PORT', 12345)),
        help='Server port (default: 12345 or env SERVER_PORT)'
    )
    parser.add_argument(
        '--k8s',
        action='store_true',
        help='Use Kubernetes service discovery'
    )
    
    args = parser.parse_args()
    
    # Setup service discovery
    if args.k8s:
        print("Using Kubernetes service discovery...")
        discovery = ServiceDiscovery.from_kubernetes_env()
    else:
        print(f"Using direct connection to {args.host}:{args.port}...")
        discovery = ServiceDiscovery.from_direct_config(args.host, args.port)
    
    # Create client application
    app = OpenChatClientApp(discovery)
    
    try:
        # Get credentials
        print("\n" + "=" * 60)
        print("OpenChat Authentication")
        print("=" * 60)
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        if not username or not password:
            print("Username and password required")
            sys.exit(1)
        
        # Connect and authenticate
        if not await app.connect_to_server(username, password):
            print("Failed to connect to server")
            sys.exit(1)
        
        # Run interactive chat
        await app.interactive_chat()
        
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        app.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await app.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown")
        sys.exit(0)
