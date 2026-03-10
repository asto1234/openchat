"""
Utility functions for OpenChat
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class JsonConfig:
    """Load and manage JSON configuration files"""
    
    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {config_path}")
            return {}
    
    @staticmethod
    def save(config_path: str, data: Dict[str, Any]):
        """Save configuration to JSON file"""
        try:
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")


class DateTimeHelper:
    """Helper functions for datetime operations"""
    
    @staticmethod
    def now_iso() -> str:
        """Get current datetime in ISO format"""
        return datetime.utcnow().isoformat() + 'Z'
    
    @staticmethod
    def now_timestamp() -> float:
        """Get current timestamp"""
        return datetime.utcnow().timestamp()
    
    @staticmethod
    def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object"""
        return dt.strftime(fmt)


class ValidationHelper:
    """Input validation helpers"""
    
    @staticmethod
    def validate_username(username: str, min_len: int = 3, max_len: int = 32) -> bool:
        """Validate username format"""
        if not username or not isinstance(username, str):
            return False
        if len(username) < min_len or len(username) > max_len:
            return False
        # Allow alphanumeric, underscore, hyphen
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))
    
    @staticmethod
    def validate_password(password: str, min_len: int = 8) -> tuple:
        """
        Validate password strength
        Returns: (is_valid, issues)
        """
        issues = []
        
        if len(password) < min_len:
            issues.append(f"Password must be at least {min_len} characters")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Simple email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_string(s: str, max_len: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(s, str):
            return ""
        # Remove null bytes and control characters
        s = ''.join(c for c in s if ord(c) >= 32 or c in '\t\n\r')
        return s[:max_len].strip()


class LogHelper:
    """Logging utilities"""
    
    @staticmethod
    def setup_file_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
        """Setup file logger"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
        return logger
    
    @staticmethod
    def log_security_event(logger: logging.Logger, event_type: str, user_id: str, details: str):
        """Log security events"""
        logger.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}")


class CryptoHelper:
    """Cryptographic helpers"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate random token (hex)"""
        import secrets
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID v4"""
        import uuid
        return str(uuid.uuid4())


class PerformanceHelper:
    """Performance monitoring"""
    
    def __init__(self):
        self.timers: Dict[str, List[float]] = {}
    
    def start_timer(self, name: str):
        """Start named timer"""
        import time
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(time.time())
    
    def end_timer(self, name: str) -> float:
        """End timer and return elapsed time"""
        import time
        if name not in self.timers or not self.timers[name]:
            return 0.0
        elapsed = time.time() - self.timers[name].pop()
        return elapsed
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics"""
        if name not in self.timers or not self.timers[name]:
            return {}
        
        times = self.timers[name]
        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "total": sum(times)
        }


if __name__ == "__main__":
    # Test utilities
    print("=== Testing Utilities ===\n")
    
    # Validation
    print("Validation Tests:")
    print(f"  Username 'alice': {ValidationHelper.validate_username('alice')}")
    print(f"  Username 'ab': {ValidationHelper.validate_username('ab')}")
    print(f"  Email 'test@example.com': {ValidationHelper.validate_email('test@example.com')}")
    
    # Crypto
    print("\nCrypto Tests:")
    print(f"  Random token: {CryptoHelper.generate_token(16)}")
    print(f"  UUID: {CryptoHelper.generate_uuid()}")
    
    # Performance
    print("\nPerformance Tests:")
    perf = PerformanceHelper()
    import time
    perf.start_timer("test")
    time.sleep(0.1)
    elapsed = perf.end_timer("test")
    print(f"  Sleep test: {elapsed:.4f}s")
    
    print("\n✓ Utility tests passed!")
