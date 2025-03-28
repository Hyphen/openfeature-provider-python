# Contributing

Thank you for your interest in contributing to the OpenFeature Hyphen Provider! This document provides guidelines and steps for contributing.

## Code of Conduct

Contributors are expected to maintain a respectful and inclusive environment for everyone involved in the project.

## Development Setup

1. Fork and clone the repository
2. Install Poetry (package manager) if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Run tests:
   ```bash
   poetry run pytest
   ```

## Pull Request Process

1. Fork this repository to your account
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and test them:
   - Run `poetry install` to install dependencies
   - Run `poetry run pytest` to run tests
   - Run code quality checks:
     ```bash
     poetry run black .
     poetry run isort .
     poetry run mypy .
     poetry run ruff check .
     ```
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to your branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Before Submitting a PR

- Ensure all tests pass
- Add tests for new features
- Update documentation as needed
- Follow existing code style (Black formatting)
- Write clear commit messages
- Update examples if needed

## Project Structure

```
openfeature-provider-python/
├── src/
│   └── openfeature_provider_hyphen/  # Main provider implementation
├── examples/                         # Usage examples
└── tests/                           # Test files
```

## Creating Issues

- Search for existing issues first
- Provide clear reproduction steps
- Include relevant versions:
  - Python version
  - openfeature-provider-python version
  - openfeature-sdk version
  - Operating system

## Need Help?

Feel free to ask questions by creating an issue or starting a discussion.

For detailed information about creating pull requests, see the [Github documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).
