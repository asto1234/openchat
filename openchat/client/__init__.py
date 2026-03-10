"""Client module - Client implementations."""

try:
    from openchat.client.architecture import CleanChatClient
except ImportError:
    CleanChatClient = None

try:
    from openchat.client.secure import SecureClient
except ImportError:
    SecureClient = None

try:
    from openchat.client.basic import BasicClient
except ImportError:
    BasicClient = None

__all__ = [
    "CleanChatClient",
    "SecureClient",
    "BasicClient",
]
