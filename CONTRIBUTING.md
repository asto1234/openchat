# Contributing to OpenChat

Thank you for your interest in contributing to OpenChat! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on ideas, not individuals
- Report issues responsibly

## Getting Started

### 1. Setup Development Environment

```bash
git clone https://github.com/openchat/openchat.git
cd openchat
./scripts/install_dev.sh
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
```

## Development Workflow

### Code Style

We follow PEP 8 with these tools:

**Black** (formatting)
```bash
black openchat tests examples --line-length 100
```

**isort** (import sorting)
```bash
isort openchat tests examples --profile black
```

**Ruff** (linting)
```bash
ruff check openchat tests examples
```

**mypy** (type checking)
```bash
mypy openchat
```

Run all formatting tools:
```bash
./scripts/format_code.sh
```

### Code Quality

Before submitting, ensure code passes all checks:

```bash
# Format code
./scripts/format_code.sh

# Run linting
./scripts/lint.sh

# Run tests
./scripts/run_tests.sh tests/

# Check coverage
pytest tests/ --cov=openchat --cov-report=html
```

### Type Hints

Add type hints to all functions:

```python
from typing import Optional, List
from openchat.crypto import E2EEncryption

def encrypt_messages(
    messages: List[str],
    encryption: E2EEncryption,
    sign: Optional[bool] = False
) -> List[bytes]:
    """Encrypt multiple messages.
    
    Args:
        messages: List of messages to encrypt
        encryption: Encryption handler
        sign: Whether to sign messages (default: False)
        
    Returns:
        List of encrypted message bytes
    """
    return [encryption.encrypt_message(msg) for msg in messages]
```

### Docstrings

Use Google-style docstrings:

```python
def connect(self, host: str, port: int) -> bool:
    """Connect to remote server.
    
    Args:
        host: Server hostname or IP address
        port: Server port number
        
    Returns:
        True if connection successful, False otherwise
        
    Raises:
        ConnectionError: If connection fails
        TimeoutError: If connection times out
        
    Example:
        >>> client = ChatClient()
        >>> client.connect("localhost", 9000)
        True
    """
    pass
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_encryption.py -v

# Specific test
pytest tests/unit/test_encryption.py::TestEncryption::test_key_exchange -v

# With coverage
pytest tests/ --cov=openchat --cov-report=html

# Run benchmarks
pytest benchmarks/ -v
```

### Writing Tests

Create test files in appropriate directories:

```
tests/
├── unit/test_my_feature.py         # Unit tests
├── integration/test_integration.py # Integration tests
└── fixtures/test_data.py           # Shared fixtures
```

Example test:

```python
import pytest
from openchat.crypto import E2EEncryption, SecurityManager


class TestMyFeature:
    """Test suite for my feature."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        self.security = SecurityManager()
        self.encryption = E2EEncryption(
            self.security.generate_key_pair()
        )

    def test_basic_functionality(self):
        """Test basic functionality."""
        result = self.encryption.encrypt_message(b"test")
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operation."""
        result = await some_async_function()
        assert result is not None

    @pytest.mark.parametrize("message", [
        b"short",
        b"a" * 1000,
        b"special!@#$%",
    ])
    def test_various_inputs(self, message):
        """Test with various inputs."""
        result = self.encryption.encrypt_message(message)
        assert result is not None
```

### Test Coverage

Aim for >85% coverage:

```bash
pytest tests/ --cov=openchat --cov-report=term-missing
```

## Commit Messages

Use clear, descriptive commit messages:

```
[TYPE] Brief description (50 chars max)

More detailed explanation if needed. Wrap at 72 characters.
Explain WHY, not WHAT (code shows what).

Fixes #issue_number
Related to #other_issue
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test additions/changes
- `perf`: Performance improvement
- `refactor`: Code refactoring
- `ci`: CI/CD changes
- `chore`: Dependency updates, etc.

Examples:
```
feat: Add encryption support for messages
fix: Resolve race condition in database transactions
test: Add benchmarks for key exchange operations
docs: Document new server configuration options
perf: Optimize message summarization
```

## Pull Requests

### Before Submitting

1. Update from main branch:
```bash
git fetch origin
git rebase origin/main
```

2. Run full test suite:
```bash
./scripts/format_code.sh
./scripts/lint.sh
pytest tests/ --cov=openchat
```

3. Update documentation if needed

### PR Description Template

```markdown
## Description
Brief description of changes

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Performance improvement

## Related Issues
Fixes #issue_number
Related to #other_issue

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Changes are backwards compatible
```

## Documentation

### Docstring Style

Use Google-style docstrings (see Testing section above).

### Adding Documentation

1. **API Documentation**: Update docstrings in source code
2. **Tutorials**: Add to `docs/source/tutorials/`
3. **Architecture Docs**: Add to `docs/source/architecture/`

### Building Documentation

```bash
cd docs
sphinx-build -b html source build
open build/index.html
```

## Performance

### Benchmarking

Add benchmarks for performance-critical code:

```python
# benchmarks/crypto/bench_encryption.py
import pytest
from openchat.crypto import E2EEncryption

def test_encryption_performance(benchmark):
    """Benchmark encryption speed."""
    encryption = E2EEncryption(...)
    
    def encrypt():
        return encryption.encrypt_message(b"test message")
    
    result = benchmark(encrypt)
    assert result is not None
```

Run benchmarks:
```bash
pytest benchmarks/ -v
pytest benchmarks/crypto/ --benchmark-only
```

## Release Process

1. Update version in `openchat/__init__.py`
2. Update [CHANGELOG.md](CHANGELOG.md)
3. Create git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions will publish to PyPI

## Issues and Bug Reports

### Reporting Bugs

Include:
- Python version
- OS and version
- Minimal reproduction code
- Expected vs actual behavior
- Traceback/error messages

### Feature Requests

Include:
- Clear description of feature
- Why it's needed
- Example usage
- Potential impact

## Questions and Discussions

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use Issues for bugs and feature requests
- **Email**: Contact team@openchat.dev for security issues

## Legal

By contributing, you agree that:
- Your contributions will be licensed under MIT License
- You have the right to make these contributions
- You grant OpenChat rights to use your contributions

## Review Process

Maintainers will:
1. Review code quality and tests
2. Check compatibility and performance
3. Verify documentation
4. Request changes if needed
5. Merge approved PRs

Thanks for contributing! 🎉
