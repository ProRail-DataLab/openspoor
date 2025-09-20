# Contributing

We welcome contributions to OpenSpoor! This guide will help you get started with contributing to the project.

## Quick Start

1. Fork the repository on GitHub
2. Set up the development environment (see [Development Setup](setup.md))
3. Create a feature branch
4. Make your changes
5. Run tests and quality checks
6. Submit a pull request

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

- A clear description of the issue
- Steps to reproduce the problem
- Expected vs actual behavior
- Your environment (Python version, OS, OpenSpoor version)
- Any relevant error messages or logs

### Feature Requests

For new features, please:

- Check if the feature already exists or is planned
- Describe the use case and benefits
- Provide examples of how the feature would be used
- Consider implementation complexity

### Code Contributions

We accept contributions for:

- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/openspoor.git
cd openspoor
```

### 2. Set Up Development Environment

Follow the [Development Setup](setup.md) guide to install dependencies and tools.

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Changes

- Write clear, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 5. Test Your Changes

```bash
# Run tests
uv run pytest --nbmake --nbmake-kernel=python3

# Run quality checks
pre-commit run --all-files

# Check test coverage
uv run pytest --cov=openspoor --cov-report=html
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "Add your feature"
```

Use clear, descriptive commit messages following the conventional commits format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/modifications
- `refactor:` for code refactoring

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:

- Clear title and description
- Reference to any related issues
- Screenshots for UI changes
- At least three reviewers assigned

## Code Standards

### Python Style

We follow PEP 8 and use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Code Quality Requirements

- All code must pass pre-commit hooks
- Test coverage should not decrease
- New features require tests
- Public APIs require documentation
- Type hints are required for new code

### Documentation Standards

- Use NumPy-style docstrings
- Include examples in docstrings
- Update relevant documentation files
- Add new features to the changelog

Example docstring:

```python
def example_function(param1: str, param2: int = 10) -> bool:
    """
    Brief description of the function.

    Longer description explaining the purpose and usage of the function.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int, optional
        Description of param2, by default 10.

    Returns
    -------
    bool
        Description of return value.

    Examples
    --------
    >>> result = example_function("test", 5)
    >>> print(result)
    True
    """
    return len(param1) > param2
```

## Testing Guidelines

### Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── test_mapservices/
├── test_transformers/
├── test_visualisations/
├── test_network/
└── test_spoortakmodel/
```

### Writing Tests

- Use pytest framework
- Follow AAA pattern (Arrange, Act, Assert)
- Test both success and failure cases
- Use meaningful test names
- Mock external dependencies

Example test:

```python
import pytest
from openspoor.transformers import TransformerGeocodeToCoordinates

def test_transformer_geocode_to_coordinates_valid_input():
    """Test coordinate transformation with valid input."""
    # Arrange
    transformer = TransformerGeocodeToCoordinates(
        geocode_column='geocode',
        geocode_km_column='km',
        coordinate_system='EPSG:28992'
    )
    data = pd.DataFrame({
        'geocode': ['001', '002'],
        'km': [10.0, 20.0]
    })
    
    # Act
    result = transformer.transform(data)
    
    # Assert
    assert 'x' in result.columns
    assert 'y' in result.columns
    assert len(result) == 2
```

### Test Coverage

- Aim for >90% test coverage
- Focus on testing public APIs
- Include integration tests for complex workflows
- Test error conditions and edge cases

## Documentation

### API Documentation

API documentation is automatically generated from docstrings using MkDocs and mkdocstrings.

### User Guides

User guides should include:

- Clear explanations of concepts
- Code examples with expected output
- Common use cases
- Integration with other modules

### Examples

The demo notebook should showcase:

- Real-world use cases
- Best practices
- Integration examples
- Performance considerations

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release PR
5. Tag release after merge
6. Update documentation

## Getting Help

### Discussion Channels

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Code reviews: Feedback on pull requests

### Mentorship

New contributors are welcome! If you need help:

- Comment on issues labeled "good first issue"
- Ask questions in pull request reviews
- Reach out to maintainers for guidance

## Recognition

Contributors are recognized in:

- CONTRIBUTORS.md file
- Release notes
- Annual contributor highlights

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read and follow our Code of Conduct.

## License

By contributing to OpenSpoor, you agree that your contributions will be licensed under the MIT License.