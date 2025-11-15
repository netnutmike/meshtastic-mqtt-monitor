# Contributing to Meshtastic MQTT Monitor

Thank you for your interest in contributing to the Meshtastic MQTT Monitor! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Development Workflow](#development-workflow)

## Code of Conduct

This project follows the Meshtastic community guidelines. Be respectful, inclusive, and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/meshtastic-mqtt-monitor.git
   cd meshtastic-mqtt-monitor
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/meshtastic/meshtastic-mqtt-monitor.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- git

### Install Development Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests to ensure everything is working
pytest

# Check code formatting
black --check src/ tests/

# Run linter
flake8 src/ tests/

# Run type checker
mypy src/
```

## Code Style Guidelines

We follow Python best practices and use automated tools to maintain code quality.

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Use [mypy](http://mypy-lang.org/) for type checking

### Black Configuration

Black is configured in `pyproject.toml`:
- Line length: 100 characters
- Target Python versions: 3.8+

**Format your code before committing**:
```bash
black src/ tests/
```

**Check formatting without modifying files**:
```bash
black --check src/ tests/
```

### Flake8 Configuration

Run Flake8 to check for style issues:
```bash
flake8 src/ tests/
```

Common issues to avoid:
- Unused imports
- Undefined variables
- Lines too long (>100 characters)
- Missing whitespace around operators
- Trailing whitespace

### Type Hints

- Use type hints for function arguments and return values
- Use `Optional[Type]` for nullable values
- Use `List[Type]`, `Dict[Key, Value]` for collections
- Run mypy to check type consistency:
  ```bash
  mypy src/
  ```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def decode_message(payload: bytes, channel: str) -> DecodedMessage:
    """
    Decode a Meshtastic protobuf message.
    
    Args:
        payload: Raw message bytes
        channel: Channel name for decryption key lookup
        
    Returns:
        DecodedMessage object with parsed fields
        
    Raises:
        ValueError: If payload is invalid or cannot be decoded
    """
    # Implementation
```

### Code Organization

- Keep functions focused and single-purpose
- Limit function length to ~50 lines when possible
- Use meaningful variable and function names
- Add comments for complex logic
- Group related functionality into classes
- Separate concerns into different modules

### Import Organization

Organize imports in the following order:
1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
import os
from typing import Dict, List, Optional

import yaml
from cryptography.hazmat.primitives.ciphers import Cipher

from src.config import MonitorConfig
from src.decoder import MessageDecoder
```

## Testing Requirements

All code contributions must include appropriate tests.

### Test Framework

We use [pytest](https://pytest.org/) for testing:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_decoder.py

# Run specific test function
pytest tests/test_decoder.py::test_decode_position_message

# Run with verbose output
pytest -v
```

### Test Coverage

- Aim for 80%+ code coverage for new code
- All new features must include tests
- Bug fixes should include regression tests
- Run coverage report:
  ```bash
  pytest --cov=src --cov-report=html
  # Open htmlcov/index.html in browser
  ```

### Writing Tests

#### Unit Tests

Test individual functions and methods in isolation:

```python
def test_decode_position_message():
    """Test decoding of position/location messages."""
    decoder = MessageDecoder(channel_keys={})
    
    # Create test payload
    payload = create_test_position_payload(
        latitude=37.7749,
        longitude=-122.4194,
        altitude=15
    )
    
    # Decode message
    result = decoder.decode("msh/US/2/e/LongFast", payload)
    
    # Assert expected results
    assert result.packet_type == "POSITION"
    assert result.fields["latitude"] == 37.7749
    assert result.fields["longitude"] == -122.4194
    assert result.fields["altitude"] == 15
```

#### Integration Tests

Test interaction between multiple components:

```python
def test_end_to_end_message_flow(mock_mqtt_broker):
    """Test complete message flow from MQTT to formatted output."""
    config = ConfigManager.get_default_config()
    monitor = MeshtasticMonitor(config)
    
    # Simulate MQTT message
    mock_mqtt_broker.publish("msh/US/2/e/LongFast", test_payload)
    
    # Verify message was processed
    assert monitor.message_count == 1
```

#### Test Organization

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Group related tests in classes: `class TestDecoder:`
- Use fixtures for common setup
- Use parametrize for testing multiple inputs

#### Mocking

Use `pytest-mock` for mocking external dependencies:

```python
def test_mqtt_connection(mocker):
    """Test MQTT connection handling."""
    mock_client = mocker.patch('paho.mqtt.client.Client')
    
    mqtt = MQTTClient(config, callback)
    mqtt.connect()
    
    mock_client.return_value.connect.assert_called_once()
```

### Test Best Practices

- Test one thing per test function
- Use descriptive test names
- Keep tests simple and readable
- Avoid testing implementation details
- Test edge cases and error conditions
- Use fixtures for reusable test data
- Clean up resources in teardown

## Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Run all checks**:
   ```bash
   # Format code
   black src/ tests/
   
   # Run linter
   flake8 src/ tests/
   
   # Run type checker
   mypy src/
   
   # Run tests
   pytest --cov=src
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```
   
   Use clear, descriptive commit messages:
   - Start with a verb: "Add", "Fix", "Update", "Remove"
   - Keep first line under 72 characters
   - Add detailed description if needed

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting the Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template:
   - **Title**: Clear, concise description
   - **Description**: What changes were made and why
   - **Related Issues**: Link to related issues
   - **Testing**: Describe how you tested the changes
   - **Screenshots**: If applicable

### PR Review Process

1. **Automated Checks**: CI will run tests and linting
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainers will merge

### After Merge

1. **Delete your branch**:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**:
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

## Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported in [Issues](https://github.com/meshtastic/meshtastic-mqtt-monitor/issues)
2. Verify you're using the latest version
3. Try to reproduce the bug with minimal configuration

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With configuration '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 13]
- Python version: [e.g., 3.10.5]
- Package version: [e.g., 0.1.0]

**Configuration:**
```yaml
# Relevant parts of your config.yaml
```

**Logs/Output:**
```
# Error messages or relevant output
```

**Additional context**
Any other information about the problem.
```

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other context, mockups, or examples.

**Would you be willing to implement this?**
Yes/No - If yes, we can guide you through the process.
```

## Development Workflow

### Adding a New Feature

1. **Discuss first**: Open an issue to discuss the feature
2. **Design**: Plan the implementation approach
3. **Implement**: Write code following guidelines
4. **Test**: Add comprehensive tests
5. **Document**: Update README and docstrings
6. **Submit**: Create a pull request

### Fixing a Bug

1. **Reproduce**: Confirm the bug exists
2. **Identify**: Find the root cause
3. **Fix**: Implement the fix
4. **Test**: Add regression test
5. **Verify**: Ensure fix works and doesn't break anything
6. **Submit**: Create a pull request

### Adding Support for New Packet Types

1. **Research**: Study the Meshtastic protobuf definition
2. **Decoder**: Add decoding logic in `src/decoder.py`
3. **Formatter**: Add display fields in `src/formatter.py`
4. **Config**: Add default configuration in `src/config.py`
5. **Tests**: Add tests for the new packet type
6. **Documentation**: Update README and config.example.yaml

### Improving Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples or use cases
- Improve code comments
- Update outdated information

## Questions?

If you have questions about contributing:
- Open a [Discussion](https://github.com/meshtastic/meshtastic-mqtt-monitor/discussions)
- Ask in the [Meshtastic Discord](https://discord.gg/meshtastic)
- Comment on a related issue

## Thank You!

Your contributions help make this project better for everyone. We appreciate your time and effort!

---

Happy coding! 🚀
