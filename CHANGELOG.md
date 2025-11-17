# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-17

### Added
- Initial release of Ethical Meat DB scraper
- Core scraping functionality for Essen mit Herz website
- Support for extracting animal welfare ratings
- Label and product page parsing
- HTML caching to avoid repeated requests
- Configurable rate limiting
- JSON and CSV output formats
- Command-line interface with multiple options
- Modern Python package structure with pyproject.toml
- Comprehensive test suite
- GitHub Actions CI/CD workflow
- Development tooling (Makefile, pre-commit hooks)
- Example usage scripts
- Full documentation in README.md
- Contributing guidelines
- MIT License

### Features
- Discover all label URLs from the EMH website
- Parse label pages to extract product links
- Extract rating tiers (TOP, OK, UNCOOL, NO GO)
- Calculate steps to reach TOP tier
- Standardize animal type identification
- Smart caching with MD5 URL hashing
- Respectful rate limiting (default 1s between requests)

[0.1.0]: https://github.com/entropicbloom/ethicalmeat-db/releases/tag/v0.1.0
