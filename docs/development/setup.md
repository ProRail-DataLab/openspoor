# Development Setup

This guide will help you set up a development environment for contributing to OpenSpoor.

## Prerequisites

- Python 3.10 or higher
- Git
- uv package manager (recommended) or pip

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/ProRail-DataLab/openspoor.git
cd openspoor
```

### Step 2: Install uv (if not already installed)

uv is the recommended package manager for this project:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Step 3: Create Virtual Environment

```bash
uv venv --python=3.11
```

### Step 4: Activate Virtual Environment

```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Step 5: Install Dependencies

```bash
# Install all dependencies including development tools
uv sync

# Or install only the package
uv pip install -e .
```

### Step 6: Install Pre-commit Hooks

Pre-commit hooks ensure code quality before commits:

```bash
pre-commit install
```

### Step 7: Verify Setup

Run tests to verify everything is working:

```bash
uv run pytest --nbmake --nbmake-kernel=python3
```

## Development Tools

### Package Manager: uv

uv is a fast Python package manager that we use for:

- Dependency management
- Virtual environment creation
- Package building
- Running scripts

Common uv commands:

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add development dependency
uv add --group dev package-name

# Run Python with uv
uv run python script.py

# Run tests
uv run pytest

# Build package
uv build
```

### Code Quality Tools

#### Black (Code Formatting)

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .
```

#### isort (Import Sorting)

```bash
# Sort imports
isort .

# Check import sorting
isort --check-only .
```

#### flake8 (Linting)

```bash
# Run linting
flake8 openspoor tests

# With specific configuration
flake8 --config=setup.cfg
```

#### mypy (Type Checking)

```bash
# Run type checking
mypy openspoor

# Check specific file
mypy openspoor/mapservices/find_mapservice.py
```

### Pre-commit Hooks

Pre-commit automatically runs quality checks before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openspoor

# Run specific test file
uv run pytest tests/test_mapservices/

# Run tests including notebooks
uv run pytest --nbmake --nbmake-kernel=python3

# Run tests in parallel
uv run pytest -n auto
```

### Test Configuration

Tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Coverage Reports

```bash
# Generate coverage report
uv run pytest --cov=openspoor --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Documentation

### Building Documentation

```bash
# Install documentation dependencies
uv sync --group docs

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### API Documentation

API documentation is generated automatically from docstrings:

```bash
# Generate API docs (included in mkdocs build)
mkdocs build
```

### Legacy Documentation

The project also supports pdoc for API documentation:

```bash
# Serve API docs with pdoc
pdoc --http : openspoor
```

## Environment Variables

For development, you may need to set certain environment variables:

```bash
# Example: Enable debug mode
export OPENSPOOR_DEBUG=1

# Example: Use custom config file
export OPENSPOOR_CONFIG=/path/to/custom/config.yaml
```

## IDE Configuration

### Visual Studio Code

Recommended extensions:

- Python
- Pylance
- Black Formatter
- isort
- GitLens

Example `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm

Configure PyCharm to use:

- Virtual environment: `.venv/bin/python`
- Code style: Black
- Import organizer: isort
- Type checker: mypy

## Debugging

### Debug Configuration

For debugging with breakpoints:

```python
import pdb; pdb.set_trace()  # Built-in debugger

# Or use IPython debugger
import ipdb; ipdb.set_trace()
```

### Logging

OpenSpoor uses loguru for logging:

```python
from loguru import logger

logger.info("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

## Performance Profiling

### Memory Profiling

```bash
# Install memory profiler
uv add --group dev memory-profiler

# Profile memory usage
python -m memory_profiler script.py
```

### CPU Profiling

```bash
# Profile with cProfile
python -m cProfile -o profile.stats script.py

# Analyze results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

## Troubleshooting

### Common Issues

#### Virtual Environment Issues

```bash
# Remove and recreate virtual environment
rm -rf .venv
uv venv --python=3.11
source .venv/bin/activate
uv sync
```

#### Dependency Conflicts

```bash
# Clear uv cache
uv cache clean

# Update lock file
uv lock --upgrade
```

#### GeoPandas Installation Issues

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install gdal-bin libgdal-dev

# Use conda for complex dependencies
conda install geopandas
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting guide](testing.md)
2. Search [GitHub Issues](https://github.com/ProRail-DataLab/openspoor/issues)
3. Create a new issue with:
   - Detailed error message
   - Steps to reproduce
   - Environment information
   - Operating system and Python version

## Next Steps

Once your development environment is set up:

1. Review the [Contributing Guide](contributing.md)
2. Look for issues labeled "good first issue"
3. Read the codebase to understand the architecture
4. Start with small improvements or bug fixes
5. Gradually work on larger features