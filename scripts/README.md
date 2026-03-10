# OpenChat Scripts

Utility scripts for development, testing, and deployment of OpenChat.

## Available Scripts

### `install_dev.sh`
Sets up the development environment.

```bash
./scripts/install_dev.sh
```

This script:
- Checks Python version (requires 3.11+)
- Creates a virtual environment
- Installs all dependencies including dev tools
- Sets up pre-commit hooks

### `format_code.sh`
Formats code using black and isort.

```bash
./scripts/format_code.sh
```

Applies:
- Import sorting with isort
- Code formatting with black (100 char line length)

### `lint.sh`
Runs linting and type checks.

```bash
./scripts/lint.sh
```

Performs:
- Ruff static analysis
- mypy type checking
- flake8 style checking

### `run_tests.sh`
Runs the test suite.

```bash
./scripts/run_tests.sh           # Run all tests
./scripts/run_tests.sh tests/    # Run all tests with coverage
./scripts/run_tests.sh tests/unit/test_encryption.py  # Run specific test file
```

Options:
- `--coverage`: Generate HTML coverage report

### `build_docker.sh`
Builds the Docker image.

```bash
./scripts/build_docker.sh          # Build image
./scripts/build_docker.sh --test   # Build and test image
```

Creates images tagged with:
- `openchat:X.Y.Z` (version-specific)
- `openchat:latest`

## Development Workflow

1. **Setup**: `./scripts/install_dev.sh`
2. **Code**: Edit files in `openchat/`
3. **Format**: `./scripts/format_code.sh`
4. **Lint**: `./scripts/lint.sh`
5. **Test**: `./scripts/run_tests.sh tests/`
6. **Build**: `./scripts/build_docker.sh`

## Making Scripts Executable

On Linux/macOS:
```bash
chmod +x scripts/*.sh
```

On Windows (using Git Bash):
Scripts should work with Git Bash or WSL.

## Dependencies

Scripts require:
- Python 3.11+
- Docker (for `build_docker.sh`)
- bash shell (Linux/macOS or Git Bash on Windows)

Install Python tools:
```bash
pip install -e '.[dev,docs]'
```
