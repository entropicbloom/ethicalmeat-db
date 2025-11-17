# Contributing to Ethical Meat DB

Thank you for your interest in contributing to Ethical Meat DB! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, constructive, and helpful. We're all here to make ethical meat consumption data more accessible.

## Getting Started

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone https://github.com/entropicbloom/ethicalmeat-db.git
cd ethicalmeat-db

# Set up development environment
make dev-setup
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

## Development Workflow

### Running Tests

Before submitting changes, ensure all tests pass:

```bash
# Run tests
make test

# Run tests with coverage
make test-cov
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code (black + isort)
make format

# Check formatting
make format-check

# Run linters
make lint

# Run all checks (format, lint, test)
make check
```

### Code Style Guidelines

- **Line length**: Maximum 100 characters
- **Formatting**: Use `black` for Python code formatting
- **Import sorting**: Use `isort` with black profile
- **Type hints**: Add type hints where appropriate
- **Docstrings**: Use Google-style docstrings

Example:
```python
def parse_product_page(self, url: str) -> Dict[str, Any]:
    """Parse a product page to extract rating information.

    Args:
        url: The URL of the product page to parse

    Returns:
        Dictionary containing:
            - title: Product title
            - animal: Animal type (standardized)
            - tier: Rating tier (TOP/OK/UNCOOL/NO GO)
            - steps_to_go: Number of steps to reach TOP
    """
    # Implementation here
```

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

1. Description of the bug
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Python version and OS
6. Relevant logs or error messages

### Feature Requests

For feature requests, please describe:

1. The problem you're trying to solve
2. Your proposed solution
3. Any alternative solutions considered
4. Why this feature would benefit the project

### Code Contributions

#### Before Starting

1. Check existing issues and PRs to avoid duplication
2. For major changes, open an issue first to discuss
3. For minor changes (typos, small bugs), feel free to submit a PR directly

#### Pull Request Process

1. **Update tests**: Add or update tests for your changes
2. **Update documentation**: Update README or docstrings if needed
3. **Run all checks**: Ensure `make check` passes
4. **Commit messages**: Write clear, descriptive commit messages
5. **PR description**: Explain what changes you made and why

Example commit message:
```
Add caching support for label URLs

- Implement LRU cache for label URL discovery
- Add cache expiration configuration
- Update tests to cover caching behavior

Fixes #42
```

#### Pull Request Checklist

- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG updated (if applicable)
- [ ] Commit messages are clear and descriptive

## Project Structure

```
ethicalmeat-db/
├── src/              # Source code
├── tests/            # Test files
├── examples/         # Example scripts
├── docs/             # Documentation
└── .github/          # GitHub workflows
```

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names

Example:
```python
def test_parse_product_page_extracts_tier():
    """Test that parse_product_page correctly extracts the tier."""
    scraper = EMHScraper(cache_dir=None, rate_limit=0)
    result = scraper.parse_product_page(test_url)
    assert result['tier'] in ['TOP', 'OK', 'UNCOOL', 'NO GO']
```

### Test Coverage

Aim for high test coverage, especially for:
- Core scraping logic
- Data parsing functions
- Edge cases and error handling

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Brief description of what the function does.

    More detailed explanation if needed. Can span
    multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
```

### README Updates

If your changes affect usage or installation:
- Update the relevant sections in README.md
- Add examples if introducing new features
- Update the project structure if adding new directories

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v0.x.x -m "Release v0.x.x"`
4. Push tag: `git push origin v0.x.x`
5. GitHub Actions will handle the rest

## Getting Help

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar problems

## Recognition

Contributors will be acknowledged in:
- GitHub contributors page
- CHANGELOG.md (for significant contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! Let's help some animals together! 🐄🐷🐔
