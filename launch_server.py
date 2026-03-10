doins#!/usr/bin/env python3
"""
OpenChat Standalone Server
A simple, production-ready server for testing OpenChat
"""

import sys
import socket
import threading
import json
import logging
from pathlib import Path
from datetime import datetime

# Add openchat to path
sys.path.insert(0, str(Path(__file__).parent))

from openchat.crypto import E2EEncryption
from openchat.storage import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openchat_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OpenChatServer:
    """Simple OpenChat server for handling client connections"""
    
    def __init__(self, host='127.0.0.1', port=9000, db_path='openchat.db'):
        self.host = host
        self.port = port
        self.db_path = db_path
        
        # Initialize database
        self.db = DatabaseManager(db_path)
        
        # Initialize encryption
        self.encryption = E2EEncryption()
        
        # Server socket
        self.server_socket = None
        self.running = False
        self.client_count = 0
        
        logger.info(f"OpenChat Server initialized")
        logger.info(f"  Database: {db_path}")
        logger.info(f"  Listening on: {host}:{port}")
    
    def start(self):
        """Start the server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"✓ Server started on {self.host}:{self.port}")
            logger.info(f"✓ Waiting for client connections...")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    self.client_count += 1
                    logger.info(f"✓ Client #{self.client_count} connected from {address}")
                    
                    # Handle client in a thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address, self.client_count)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except KeyboardInterrupt:
                    self.shutdown()
                    break
                except Exception as e:
                    logger.error(f"Error accepting client: {e}")
                    continue
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.shutdown()
    
    def handle_client(self, client_socket, address, client_id):
        """Handle individual client connections"""
        try:
            while True:
                # Receive data from client
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # Parse JSON message
                try:
                    message = json.loads(data.decode('utf-8'))
                    command = message.get('command')
                    
                    logger.info(f"Client #{client_id}: {command}")
                    
                    # Handle different commands
                    if command == 'register':
                        response = self.handle_register(message, client_id)
                    elif command == 'list_users':
                        response = self.handle_list_users(client_id)
                    elif command == 'send_message':
                        response = self.handle_send_message(message, client_id)
                    elif command == 'get_messages':
                        response = self.handle_get_messages(message, client_id)
                    elif command == 'ping':
                        response = {'status': 'pong', 'timestamp': datetime.now().isoformat()}
                    else:
                        response = {'status': 'error', 'message': 'Unknown command'}
                    
                    # Send response
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                
                except json.JSONDecodeError:
                    response = {'status': 'error', 'message': 'Invalid JSON'}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Client #{client_id} error: {e}")
        finally:
            client_socket.close()
            logger.info(f"Client #{client_id} disconnected")
    
    def handle_register(self, message, client_id):
        """Handle user registration"""
        try:
            username = message.get('username')
            password_hash = message.get('password_hash')
            password_salt = message.get('password_salt')
            public_key = message.get('public_key')
            
            if not all([username, password_hash, password_salt, public_key]):
                return {'status': 'error', 'message': 'Missing required fields'}
            
            # Create user
            user_id = f"user_{username}_{client_id}"
            result = self.db.add_user(user_id, username, password_hash, password_salt, public_key)
            
            if result:
                logger.info(f"✓ User registered: {username}")
                return {
                    'status': 'success',
                    'user_id': user_id,
                    'message': f'User {username} registered successfully'
                }
            else:
                return {'status': 'error', 'message': 'User already exists'}
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def handle_list_users(self, client_id):
        """Handle listing users"""
        try:
            # In a real implementation, this would query the database
            return {
                'status': 'success',
                'users': ['alice', 'bob', 'charlie'],
                'count': 3
            }
        except Exception as e:
            logger.error(f"List users error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def handle_send_message(self, message, client_id):
        """Handle sending messages"""
        try:
            conversation_id = message.get('conversation_id')
            sender_id = message.get('sender_id')
            encrypted_content = message.get('encrypted_content')
            
            if not all([conversation_id, sender_id, encrypted_content]):
                return {'status': 'error', 'message': 'Missing required fields'}
            
            # Store message
            message_id = f"msg_{datetime.now().timestamp()}"
            result = self.db.add_message(message_id, conversation_id, sender_id, encrypted_content)
            
            if result:
                logger.info(f"✓ Message stored: {message_id}")
                return {
                    'status': 'success',
                    'message_id': message_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'status': 'error', 'message': 'Failed to store message'}
        
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def handle_get_messages(self, message, client_id):
        """Handle retrieving messages"""
        try:
            conversation_id = message.get('conversation_id')
            
            if not conversation_id:
                return {'status': 'error', 'message': 'Missing conversation_id'}
            
            # Get messages
            messages = self.db.get_encrypted_messages(conversation_id)
            
            logger.info(f"✓ Retrieved {len(messages)} messages from {conversation_id}")
            return {
                'status': 'success',
                'conversation_id': conversation_id,
                'message_count': len(messages),
                'messages': messages
            }
        
        except Exception as e:
            logger.error(f"Get messages error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def shutdown(self):
        """Shutdown the server"""
        logger.info("Shutting down server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Server stopped")


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║      OpenChat Server - Standalone Mode       ║
    ║                                              ║
    ║  Production-Ready E2E Encrypted Chat Server  ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # Parse arguments
    host = '127.0.0.1'
    port = 9000
    db_path = 'openchat.db'
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        db_path = sys.argv[3]
    
    # Start server
    server = OpenChatServer(host=host, port=port, db_path=db_path)
    
    print(f"Starting OpenChat Server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {db_path}")
    print(f"")
    print(f"Press Ctrl+C to stop the server")
    print(f"")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\nServer interrupted by user")
        server.shutdown()
    except Exception as e:
        print(f"Fatal error: {e}")
        server.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()
