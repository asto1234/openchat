"""
Secure Client for End-to-End Encrypted Chat
- ECDH key exchange for session key derivation
- AES-256-GCM encryption/decryption of messages
- NLP summarization of conversation history
- User-friendly CLI interface
"""

import asyncio
import json
import sys
import uuid
from typing import Optional, Dict
import logging
from getpass import getpass

from encryption import E2EEncryption, MessageEncryption
from nlp_summarizer import ConversationSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_BUFF_SIZE = 4096


class SecureChatClient:
    """Secure chat client with E2E encryption"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        self.host = host
        self.port = port
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        
        # Encryption
        self.encryption = E2EEncryption()
        self.message_encryption = MessageEncryption()
        self.private_key: Optional[bytes] = None
        self.public_key: Optional[bytes] = None
        
        # Session keys for each peer
        self.session_keys: Dict[str, bytes] = {}
        self.peer_public_keys: Dict[str, bytes] = {}
        
        # Conversation state
        self.current_peer: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.decrypted_messages: list = []
        
        # NLP
        self.summarizer = ConversationSummarizer()
        
        # Connection
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self):
        """Connect to server"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            logger.error(f"Failed to connect to {self.host}:{self.port}")
            return False
    
    async def send_message(self, message_dict: dict):
        """Send JSON message to server"""
        try:
            data = json.dumps(message_dict).encode('utf-8')
            header = len(data).to_bytes(4, 'big')
            self.writer.write(header + data)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def recv_message(self) -> Optional[dict]:
        """Receive JSON message from server"""
        try:
            header = await self.reader.readexactly(4)
            length = int.from_bytes(header, 'big')
            if length == 0:
                return None
            data = await self.reader.readexactly(length)
            return json.loads(data.decode('utf-8'))
        except asyncio.IncompleteReadError:
            return None
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON")
            return None
    
    async def authenticate(self):
        """Authenticate with server"""
        # Receive auth requirement
        auth_req = await self.recv_message()
        if auth_req and auth_req.get("type") == "auth_required":
            print("\n=== Authentication ===")
            print("1. Register (new user)")
            print("2. Login (existing user)")
            choice = input("Choose (1 or 2): ").strip()
            
            if choice == "1":
                await self.register()
            elif choice == "2":
                await self.login()
            else:
                print("Invalid choice")
                return False
            
            # Generate keypair
            self.private_key, self.public_key = self.encryption.generate_keypair()
            
            return True
        return False
    
    async def register(self):
        """Register new user"""
        username = input("Username (3-32 chars): ").strip()
        password = getpass("Password (min 8 chars): ")
        
        await self.send_message({
            "type": "register",
            "username": username,
            "password": password
        })
        
        response = await self.recv_message()
        if response and response.get("type") == "registration_success":
            self.user_id = response.get("user_id")
            self.username = username
            logger.info(f"✓ Registered as {username}")
            return True
        else:
            error = response.get("message", "Registration failed") if response else "Unknown error"
            logger.error(f"Registration failed: {error}")
            return False
    
    async def login(self):
        """Login existing user"""
        username = input("Username: ").strip()
        password = getpass("Password: ")
        
        await self.send_message({
            "type": "login",
            "username": username,
            "password": password
        })
        
        response = await self.recv_message()
        if response and response.get("type") == "login_success":
            self.user_id = response.get("user_id")
            self.username = username
            logger.info(f"✓ Logged in as {username}")
            return True
        else:
            error = response.get("message", "Login failed") if response else "Unknown error"
            logger.error(f"Login failed: {error}")
            return False
    
    async def perform_key_exchange(self, peer_id: str) -> bool:
        """Perform ECDH key exchange with peer"""
        logger.info(f"Starting key exchange with {peer_id}...")
        
        await self.send_message({
            "type": "key_exchange",
            "peer_id": peer_id,
            "public_key": self.public_key.decode('utf-8')
        })
        
        response = await self.recv_message()
        if response and response.get("type") == "key_exchange_success":
            peer_public_key = response.get("peer_public_key", "").encode('utf-8')
            self.peer_public_keys[peer_id] = peer_public_key
            
            # Derive shared secret
            session_key = self.encryption.derive_shared_secret(self.private_key, peer_public_key)
            self.session_keys[peer_id] = session_key
            
            logger.info(f"✓ Key exchange successful with {peer_id}")
            return True
        else:
            logger.error("Key exchange failed")
            return False
    
    async def send_encrypted_message(self, peer_id: str, plaintext: str) -> bool:
        """Encrypt and send message"""
        if peer_id not in self.session_keys:
            logger.warning(f"No session key with {peer_id}. Performing key exchange...")
            if not await self.perform_key_exchange(peer_id):
                return False
        
        session_key = self.session_keys[peer_id]
        encrypted_content = self.encryption.encrypt_message(session_key, plaintext)
        
        await self.send_message({
            "type": "send_message",
            "peer_id": peer_id,
            "encrypted_content": encrypted_content
        })
        
        # Store locally (with timestamp)
        self.decrypted_messages.append(f"You: {plaintext}")
        logger.info("✓ Message sent (encrypted)")
        return True
    
    async def handle_incoming_message(self, msg: dict):
        """Handle incoming encrypted message from peer"""
        if msg.get("type") == "new_message":
            from_user = msg.get("from")
            encrypted_content = msg.get("encrypted_content")
            conversation_id = msg.get("conversation_id")
            
            if from_user not in self.session_keys:
                logger.warning(f"No session key with {from_user}")
                return
            
            session_key = self.session_keys[from_user]
            plaintext = self.encryption.decrypt_message(session_key, encrypted_content)
            
            if plaintext:
                print(f"\n[{from_user}]: {plaintext}")
                self.decrypted_messages.append(f"{from_user}: {plaintext}")
                logger.info(f"Message decrypted from {from_user}")
            else:
                logger.error(f"Failed to decrypt message from {from_user}")
    
    async def request_summary(self, peer_id: str):
        """Request conversation summary from server"""
        print(f"\nGenerating summary with {peer_id}...")
        
        await self.send_message({
            "type": "get_summary",
            "peer_id": peer_id
        })
        
        response = await self.recv_message()
        if response and response.get("type") == "summary":
            server_summary = response.get("summary")
            message_count = response.get("message_count", 0)
            
            print(f"\n=== Summary ({message_count} messages) ===")
            print(server_summary)
            
            # Generate local NLP summary if we have decrypted messages
            if self.decrypted_messages:
                print("\n=== NLP Generated Summary ===")
                nlp_summary = self.summarizer.generate_session_summary(self.decrypted_messages)
                print(f"Overview: {nlp_summary['summary']}")
                print(f"Topics: {', '.join(nlp_summary['topics'])}")
                print(f"Messages in session: {nlp_summary['message_count']}")
    
    async def list_users(self):
        """List all connected users"""
        await self.send_message({"type": "list_users"})
        response = await self.recv_message()
        
        if response and response.get("type") == "user_list":
            users = response.get("users", [])
            print("\n=== Connected Users ===")
            for user in users:
                if user != self.user_id:
                    print(f"  - {user}")
    
    async def read_server_messages(self):
        """Read messages from server"""
        while True:
            msg = await self.recv_message()
            if not msg:
                logger.info("Server connection closed")
                break
            
            if msg.get("type") == "new_message":
                await self.handle_incoming_message(msg)
            elif msg.get("type") in ["error", "summary", "user_list"]:
                if msg.get("type") == "error":
                    logger.error(f"Server error: {msg.get('message')}")
    
    async def interactive_chat(self):
        """Interactive chat interface"""
        print("\n=== Secure Chat Client ===")
        print("Commands:")
        print("  /users         - List connected users")
        print("  /chat <id>     - Start chat with user")
        print("  /summary       - Get conversation summary")
        print("  /quit          - Exit")
        print()
        
        # Start reading server messages in background
        read_task = asyncio.create_task(self.read_server_messages())
        
        try:
            while True:
                command = await asyncio.to_thread(input, "> ")
                
                if command.startswith("/chat "):
                    peer_id = command.split(" ", 1)[1].strip()
                    self.current_peer = peer_id
                    self.decrypted_messages = []
                    await self.perform_key_exchange(peer_id)
                    print(f"Chat with {peer_id} started. Type messages or /back to return.")
                    await self.chat_with_peer(peer_id)
                
                elif command == "/users":
                    await self.list_users()
                
                elif command == "/summary" and self.current_peer:
                    await self.request_summary(self.current_peer)
                
                elif command == "/quit":
                    await self.send_message({"type": "disconnect"})
                    break
                
                elif command.strip():
                    if self.current_peer:
                        await self.send_encrypted_message(self.current_peer, command)
                    else:
                        print("Select a user first with /chat <id>")
        
        except KeyboardInterrupt:
            logger.info("Chat interrupted")
        finally:
            read_task.cancel()
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
    
    async def chat_with_peer(self, peer_id: str):
        """Focused chat with a single peer"""
        while True:
            message = await asyncio.to_thread(input, f"[{peer_id}]> ")
            
            if message == "/back":
                break
            elif message == "/summary":
                await self.request_summary(peer_id)
            elif message.strip():
                await self.send_encrypted_message(peer_id, message)
    
    async def run(self):
        """Main client loop"""
        if not await self.connect():
            return
        
        if not await self.authenticate():
            logger.error("Authentication failed")
            return
        
        await self.interactive_chat()


async def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure Chat Client")
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=12345, help='Server port')
    
    args = parser.parse_args()
    
    client = SecureChatClient(args.host, args.port)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
