# Contributing to Cisco Configuration Generator

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with newcomers
- **Focus on what is best** for the community

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment (venv)
- Docker (optional, for containerized development)

### First-Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cisco-config-generator.git
   cd cisco-config-generator
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/appatrous/cisco-config-generator.git
   ```

4. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

7. **Download Bootstrap files** (for UI development):
   ```bash
   chmod +x scripts/download_bootstrap.sh
   ./scripts/download_bootstrap.sh
   ```

8. **Initialize the database**:
   ```bash
   flask db upgrade
   ```

9. **Run the application**:
   ```bash
   python app.py
   ```

10. **Run tests** to verify setup:
    ```bash
    pytest
    ```

## Development Setup

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your development settings.

### Database Migrations

When changing models:

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Revert last migration
flask db downgrade
```

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

The application will be available at http://localhost:5000

## Making Changes

### Branching Strategy

We use GitHub Flow:

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Keep your branch up to date**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Branch Naming Convention

- `feature/` - New features (e.g., `feature/add-bgp-support`)
- `fix/` - Bug fixes (e.g., `fix/vlan-validation`)
- `docs/` - Documentation updates (e.g., `docs/api-examples`)
- `refactor/` - Code refactoring (e.g., `refactor/auth-module`)
- `test/` - Test additions/improvements (e.g., `test/api-coverage`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**

```
feat(api): add bulk configuration generation endpoint

fix(validator): correct VLAN ID range validation

docs(readme): update installation instructions

test(auth): add JWT token expiration tests
```

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   pytest
   pytest --cov=. --cov-report=html  # Check coverage
   ```

2. **Ensure code quality**:
   ```bash
   flake8 .
   black --check .
   pylint app.py models.py
   ```

3. **Update documentation** if needed

4. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

6. **Fill out the PR template** completely

7. **Link related issues** using keywords (e.g., "Fixes #123")

### Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests pass
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Single quotes for strings (except docstrings)
- **Imports**: Organized by stdlib, third-party, local

### Code Formatting

We use **Black** for automatic formatting:

```bash
# Format all Python files
black .

# Check without modifying
black --check .
```

### Linting

We use **flake8** and **pylint**:

```bash
# Run flake8
flake8 .

# Run pylint on specific files
pylint app.py models.py
```

### Type Hints

Use type hints for function signatures:

```python
def generate_config(platform: str, data: dict) -> str:
    """Generate configuration for specified platform."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def validate_ip_address(ip: str, version: int = 4) -> bool:
    """
    Validate an IP address.

    Args:
        ip: IP address string to validate
        version: IP version (4 or 6)

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If version is not 4 or 6

    Example:
        >>> validate_ip_address('192.168.1.1')
        True
    """
    pass
```

## Testing Guidelines

### Writing Tests

- **Location**: Place tests in the `tests/` directory
- **Naming**: `test_*.py` for files, `test_*` for functions
- **Coverage**: Aim for 80%+ code coverage
- **Isolation**: Tests should be independent

### Test Structure

```python
import pytest
from app import create_app

class TestFeature:
    """Test suite for feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        app = create_app('testing')

        # Act
        result = some_function()

        # Assert
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            some_function(invalid_input)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestAPIGenerate::test_generate_config_success

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

### Test Categories

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **API tests**: Test API endpoints
- **End-to-end tests**: Test complete workflows

## Documentation

### Code Documentation

- **Docstrings**: All public functions, classes, and modules
- **Comments**: Explain "why", not "what"
- **Type hints**: For better code understanding
- **Examples**: Include usage examples in docstrings

### API Documentation

When adding/modifying API endpoints:

1. Update `docs/API_SPEC.md`
2. Add request/response examples
3. Document all parameters
4. List possible error codes

### User Documentation

When adding features:

1. Update `README.md` if applicable
2. Add examples to relevant docs
3. Update configuration guides
4. Add to CHANGELOG.md

### Documentation Files

- `README.md`: Project overview and quick start
- `docs/API_SPEC.md`: API documentation
- `docs/ARCHITECTURE.md`: System architecture
- `docs/CCIE_GUIDE.md`: CCIE protocol coverage
- `docs/DEPLOYMENT.md`: Deployment instructions
- `docs/SECURITY.md`: Security guidelines
- `CHANGELOG.md`: Version history

## Code Review Process

### For Contributors

- Be responsive to feedback
- Make requested changes promptly
- Ask questions if feedback is unclear
- Keep discussions professional

### For Reviewers

- Be constructive and respectful
- Explain reasoning for suggestions
- Approve when ready
- Use GitHub review features

## Adding New Features

### Feature Checklist

When adding a new feature:

- [ ] Create feature branch
- [ ] Implement feature with tests
- [ ] Update documentation
- [ ] Add migration if needed
- [ ] Update API spec if applicable
- [ ] Add examples/demos
- [ ] Ensure backward compatibility
- [ ] Update CHANGELOG.md
- [ ] Create pull request

### Configuration Template Features

When adding support for new Cisco features:

1. **Research**: Understand the Cisco CLI syntax
2. **Template**: Add to appropriate `.j2` template
3. **Schema**: Update Marshmallow schemas
4. **Validation**: Add validators if needed
5. **Tests**: Add test cases
6. **Documentation**: Update CCIE_GUIDE.md

## Project Structure

```
cisco-config-generator/
├── app.py                  # Main application
├── config.py              # Configuration
├── models.py              # Database models
├── requirements.txt       # Dependencies
├── extensions/            # Flask blueprints
│   ├── api.py
│   ├── auth_routes.py
│   ├── ccie_api.py
│   └── history.py
├── utils/                 # Utilities
│   ├── auth.py
│   ├── renderer.py
│   └── validators.py
├── templates/             # Jinja2 templates
├── static/               # Static assets
├── tests/                # Test suite
├── docs/                 # Documentation
├── migrations/           # Database migrations
└── scripts/              # Utility scripts
```

## Common Tasks

### Adding a New API Endpoint

1. Add route to appropriate blueprint in `extensions/`
2. Add Marshmallow schema if needed
3. Implement validation
4. Add tests in `tests/`
5. Update `docs/API_SPEC.md`

### Adding Platform Support

1. Create new template in `templates/`
2. Add platform to `config.py` SUPPORTED_PLATFORMS
3. Update renderer in `utils/renderer.py`
4. Add platform-specific validators
5. Add tests
6. Update documentation

### Adding a Validation Rule

1. Add validator function to `utils/validators.py`
2. Add tests to `tests/test_validators.py`
3. Use in schema or route handler
4. Document in API spec

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/appatrous/cisco-config-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/appatrous/cisco-config-generator/discussions)
- **Email**: support@example.com

## Recognition

Contributors will be recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

Thank you for contributing! 🎉
