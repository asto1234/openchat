# OpenChat Repository Structure

This document describes the professional PyTorch-style repository organization of OpenChat.

## Directory Structure

```
openchat/
├── openchat/                          # Main Python package
│   ├── __init__.py                    # Package initialization
│   ├── app.py                         # Flask web application
│   │
│   ├── crypto/                        # Cryptography module
│   │   ├── __init__.py
│   │   └── encryption.py              # ECDH, AES-256-GCM, key management
│   │
│   ├── storage/                       # Database and persistence module
│   │   ├── __init__.py
│   │   └── database.py                # SQLite/PostgreSQL operations
│   │
│   ├── nlp/                           # Natural Language Processing module
│   │   ├── __init__.py
│   │   └── summarizer.py              # BART/T5-based summarization
│   │
│   ├── server/                        # Server implementations
│   │   ├── __init__.py
│   │   ├── interface.py               # Clean interface (K8s-ready)
│   │   ├── secure.py                  # Secure variant
│   │   └── basic.py                   # Basic variant
│   │
│   ├── client/                        # Client implementations
│   │   ├── __init__.py
│   │   ├── architecture.py            # Service discovery, load balancing
│   │   ├── secure.py                  # Secure variant
│   │   └── basic.py                   # Basic variant
│   │
│   └── core/                          # Core utilities
│       ├── __init__.py
│       ├── config.py                  # Configuration management
│       └── utils.py                   # Shared utilities
│
├── tests/                             # Test suite
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_encryption.py         # 15+ crypto tests
│   │   ├── test_database.py           # 12+ database tests
│   │   └── test_summarizer.py         # 8+ NLP tests
│   ├── integration/                   # Integration tests
│   │   └── __init__.py
│   ├── fixtures/                      # Shared test data and fixtures
│   │   └── __init__.py
│   ├── conftest.py                    # Pytest configuration
│   └── conftest.py                    # Shared pytest fixtures
│
├── benchmarks/                        # Performance benchmarks
│   ├── crypto/                        # Encryption benchmarks
│   │   ├── __init__.py
│   │   └── bench_encryption.py        # pytest-benchmark tests
│   ├── storage/                       # Database benchmarks
│   │   ├── __init__.py
│   │   └── bench_database.py          # pytest-benchmark tests
│   └── nlp/                           # NLP benchmarks
│       ├── __init__.py
│       └── bench_summarizer.py        # pytest-benchmark tests
│
├── examples/                          # Runnable example code
│   ├── 00_launcher.py                 # Application launcher utility
│   ├── 01_server_deployment.py        # Full server with all features
│   └── 02_client_usage.py             # Interactive client example
│
├── scripts/                           # Development and deployment scripts
│   ├── install_dev.sh                 # Setup virtual environment
│   ├── format_code.sh                 # Code formatting (black, isort)
│   ├── lint.sh                        # Linting and type checks
│   ├── run_tests.sh                   # Test runner with coverage
│   ├── build_docker.sh                # Docker image builder
│   └── README.md                      # Scripts documentation
│
├── docs/                              # Documentation
│   ├── source/
│   │   ├── api/                       # API reference
│   │   ├── tutorials/                 # Usage tutorials
│   │   └── architecture/              # Architecture and design
│   ├── k8s/                           # Kubernetes manifests
│   │   ├── configmap.yaml
│   │   ├── service.yaml
│   │   ├── deployment.yaml
│   │   └── rbac.yaml
│   └── *.md                           # Additional docs
│
├── .github/                           # GitHub configuration
│   └── workflows/                     # CI/CD workflows
│       ├── tests.yml                  # Test automation
│       ├── docker.yml                 # Docker build
│       └── publish.yml                # PyPI publishing
│
├── k8s/                               # Kubernetes manifests (symlink to docs/k8s)
│
├── .dockerignore                      # Docker ignore rules
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
├── Dockerfile                         # Container image definition
├── docker-compose.yml                 # Multi-container orchestration
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Modern Python project config (PEP 518)
├── setup.py                           # Legacy setup script
├── setup.cfg                          # Setup configuration
├── MANIFEST.in                        # Package manifest
├── LICENSE                            # MIT License
├── README.md                          # Main documentation
└── CONTRIBUTING.md                    # Contribution guidelines
```

## Module Organization

### openchat/ Package

**Main package with 6 functional submodules:**

#### 1. crypto/
Handles all cryptographic operations:
- ECDH P-256 key exchange
- AES-256-GCM message encryption
- PBKDF2 password hashing
- Session key management

```python
from openchat.crypto import SecurityManager, E2EEncryption, MessageEncryption
```

#### 2. storage/
Manages data persistence:
- User account management
- Encrypted message storage
- Conversation history
- Session summaries
- Audit logs
- Transaction support

```python
from openchat.storage import DatabaseManager, MessageStore, UserStore
```

#### 3. nlp/
Natural Language Processing:
- BART/T5-based summarization
- Conversation analysis
- Topic extraction
- Message summarization

```python
from openchat.nlp import ConversationSummarizer, MessageSummarizer
```

#### 4. server/
Server implementations:
- **interface.py** - Production-ready interface with K8s health checks
- **secure.py** - TLS-secured variant
- **basic.py** - Simple implementation

```python
from openchat.server import CleanServerInterface, SecureServerInterface, BasicServer
```

#### 5. client/
Client implementations:
- **architecture.py** - Service discovery, connection pooling, load balancing
- **secure.py** - TLS-secured variant  
- **basic.py** - Simple implementation

```python
from openchat.client import CleanChatClient, SecureClient, BasicClient
```

#### 6. core/
Core utilities:
- Configuration management
- Logging setup
- Shared utilities

```python
from openchat.core import Config, setup_logging
```

### tests/ Test Suite

Organized by test type:

**unit/** - Unit tests (35+ tests)
- Individual module functionality
- Fast execution, no external dependencies
- Files: test_encryption.py, test_database.py, test_summarizer.py

**integration/** - Integration tests
- Cross-module interactions
- End-to-end scenarios
- (Ready for implementation)

**fixtures/** - Shared test data
- Test fixtures and mock data
- Reusable test utilities

### benchmarks/ Benchmarks

Performance benchmarks for each module:

```
benchmarks/
├── crypto/bench_encryption.py         # Key exchange, encryption, decryption
├── storage/bench_database.py          # Database operations, queries
└── nlp/bench_summarizer.py            # Summarization performance
```

Run benchmarks:
```bash
pytest benchmarks/ -v
pytest benchmarks/crypto/ --benchmark-only
```

### examples/ Examples

Complete, runnable examples:

1. **00_launcher.py** - Application launcher utility
2. **01_server_deployment.py** - Full server with encryption, DB, NLP, K8s config
3. **02_client_usage.py** - Interactive client with service discovery

### scripts/ Development Scripts

Bash scripts for common tasks:

- **install_dev.sh** - Setup development environment
- **format_code.sh** - Code formatting with black/isort
- **lint.sh** - Static analysis with ruff, mypy, flake8
- **run_tests.sh** - Test execution with coverage
- **build_docker.sh** - Docker image building

### docs/ Documentation

- **source/api/** - API reference documentation
- **source/tutorials/** - Usage guides and examples
- **source/architecture/** - Architecture and design docs
- **k8s/** - Kubernetes deployment manifests

## Development Workflow

### 1. Setup

```bash
./scripts/install_dev.sh
```

Creates virtual environment, installs dependencies and dev tools.

### 2. Development

Edit files in `openchat/` submodules:

```python
# Example: openchat/crypto/encryption.py
from openchat.core import Config
from openchat.crypto import SecurityManager
```

### 3. Code Quality

```bash
# Format code
./scripts/format_code.sh

# Run linting
./scripts/lint.sh

# Run tests
./scripts/run_tests.sh tests/

# Run benchmarks
pytest benchmarks/ -v
```

### 4. Testing

**Unit Tests:**
```bash
pytest tests/unit/ -v --cov=openchat
```

**Specific Test:**
```bash
pytest tests/unit/test_encryption.py::TestEncryption::test_key_exchange -v
```

**With Coverage Report:**
```bash
pytest tests/ --cov=openchat --cov-report=html
open htmlcov/index.html
```

### 5. Building

**Docker:**
```bash
./scripts/build_docker.sh
./scripts/build_docker.sh --test
```

**Package:**
```bash
python -m build
twine check dist/*
```

## Python Version Support

- **Minimum:** Python 3.11
- **Tested:** Python 3.11, 3.12
- **Recommended:** Python 3.12+

## Dependencies

### Core
- cryptography 41.0.0+ - Cryptographic primitives
- transformers 4.30.0+ - HuggingFace models
- torch 2.0.0+ - PyTorch framework
- sqlalchemy 2.0.0+ - Database ORM
- pydantic 2.0.0+ - Data validation
- aiohttp 3.8.0+ - Async HTTP

### Development
- pytest 7.4.0+ - Testing framework
- pytest-cov - Coverage reports
- pytest-asyncio - Async test support
- black 23.0.0+ - Code formatting
- isort 5.12.0+ - Import sorting
- ruff 0.0.280+ - Fast linter
- mypy 1.4.0+ - Type checking

### Optional
- kubernetes 27.2.0+ - K8s client library
- sphinx 7.0.0+ - Documentation generation

## CI/CD Workflows

GitHub Actions workflows in `.github/workflows/`:

**tests.yml** - Test automation
- Python 3.11, 3.12 matrix
- pytest with coverage
- Linting (ruff, black, isort)
- Type checking (mypy)
- Security scans (bandit, safety)

**docker.yml** - Docker builds
- Build and push images
- Docker Compose testing
- Container security scanning (Trivy)

**publish.yml** - PyPI publishing
- Build distributions
- Publish to PyPI
- Create GitHub releases

## Installation Methods

### Development Mode
```bash
pip install -e ".[dev,docs,kubernetes]"
```

### Production
```bash
pip install openchat
```

### From Source
```bash
git clone https://github.com/openchat/openchat.git
cd openchat
pip install -e "."
```

### Docker
```bash
docker build -t openchat:latest .
docker run -it openchat:latest
```

## Project Statistics

- **Total Lines:** 8,200+
- **Source Code:** 3,500+ lines (6 submodules)
- **Tests:** 35+ automated tests (700+ lines)
- **Benchmarks:** 30+ performance tests
- **Examples:** 3 runnable examples (900+ lines)
- **Documentation:** 2,500+ lines
- **Test Coverage:** 85%+
- **CI/CD:** 3 GitHub Actions workflows

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Documentation standards

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Last Updated:** 2024
**OpenChat Version:** 1.0.0
**Python Version:** 3.11+
