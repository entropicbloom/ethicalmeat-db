# Ethical Meat Scraper 🐄🐷🐔

A Python scraper for extracting animal welfare ratings from [Essen mit Herz](https://essenmitherz.ch) (EMH), helping consumers make ethical meat and animal product choices.

## What It Does

This tool scrapes the EMH website to build a structured database mapping:
- **Labels** (e.g., Nature Suisse, Migros Weide-Beef, Natura-Beef)
- **Animals** (Rindfleisch, Kalbfleisch, Poulet, Schweinefleisch, Eier, Milch)
- **Ratings** (TOP, OK, UNCOOL, NO GO) + steps to reach TOP

## Features

- 🔍 **Robust parsing** with CSS selectors + regex fallbacks
- 💾 **Smart caching** to avoid repeated requests
- ⏱️ **Rate limiting** to be respectful to the server
- 📊 **Multiple output formats** (JSON, CSV)
- 🎯 **Clean CLI interface**

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/entropicbloom/ethicalmeat-db.git
cd ethicalmeat-db

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Development Setup

```bash
# Install with development dependencies
make dev-setup

# Or manually:
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

## Usage

### Basic Usage

```bash
# If installed as package
ethicalmeat

# Or run directly from source
python -m ethicalmeat.cli

# Using make
make run
```

This will:
- Scrape all labels and their animal products from EMH
- Save results to `emh_ratings.json` and `emh_ratings.csv`
- Show a summary of the findings

### Advanced Options

```bash
# Save to custom filename
ethicalmeat --output my_ratings

# Only JSON output
ethicalmeat --format json
# Or: make scrape-json

# Only CSV output
ethicalmeat --format csv
# Or: make scrape-csv

# Disable caching (always fetch fresh)
ethicalmeat --no-cache
# Or: make run-nocache

# Custom cache directory
ethicalmeat --cache-dir my_cache

# Slower rate limit (2 seconds between requests)
ethicalmeat --rate-limit 2.0
```

### Help

```bash
ethicalmeat --help
```

## Output Format

### JSON
```json
[
  {
    "label": "Label MIGROS WEIDE-BEEF",
    "label_url": "https://essenmitherz.ch/label-migros-weide-beef/",
    "animal": "rindfleisch",
    "product_title": "Rindfleisch Migros Weide-Beef",
    "product_url": "https://essenmitherz.ch/rindfleisch-migros-weide-beef/",
    "tier": "TOP",
    "steps_to_go": 13
  }
]
```

### CSV
```csv
label,animal,tier,steps_to_go,product_title,product_url,label_url
Label MIGROS WEIDE-BEEF,rindfleisch,TOP,13,Rindfleisch Migros Weide-Beef,...,...
```

## Project Structure

```
ethicalmeat-db/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD
├── src/
│   ├── __init__.py          # Package initialization
│   ├── scraper.py           # Core scraping logic (EMHScraper class)
│   └── cli.py               # Command-line interface
├── tests/
│   └── test_parser.py       # Test suite
├── examples/
│   └── basic_usage.py       # Example usage script
├── docs/                    # Documentation (future)
├── pyproject.toml           # Modern Python package configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── Makefile                 # Development automation
├── .env.example             # Environment configuration template
├── .gitignore               # Git ignore patterns
└── README.md                # This file
```

## How It Works

1. **Discover labels**: Scrapes the [label index page](https://essenmitherz.ch/label-und-marken/) to find all labels
2. **Parse label pages**: For each label, finds the "Produkte:" section with animal-specific links
3. **Extract ratings**: Visits each animal product page and extracts:
   - Overall tier (TOP/OK/UNCOOL/NO GO) via regex
   - Steps to reach TOP tier
   - Animal type from title or URL

The scraper uses robust parsing strategies:
- Primary: CSS selectors for structured content
- Fallback: Regex patterns on page text
- This ensures reliability even if the HTML structure changes slightly

## Rate Limiting & Caching

- **Default rate limit**: 1 second between requests (configurable)
- **Caching**: HTML responses are cached locally to avoid re-fetching
- **Cache location**: `cache/` directory (each URL hashed to a file)

## Development

### Available Make Commands

```bash
make help              # Show all available commands
make install           # Install production dependencies
make install-dev       # Install development dependencies
make dev-setup         # Complete development setup
make test              # Run tests
make test-cov          # Run tests with coverage report
make lint              # Run linting checks
make format            # Format code with black and isort
make format-check      # Check if code is formatted correctly
make clean             # Clean up cache and build artifacts
make run               # Run the scraper
make check             # Run all checks (format, lint, test)
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_parser.py -v
```

### Code Quality

```bash
# Format code
make format

# Check formatting
make format-check

# Run linters
make lint

# Run all checks
make check
```

## Contributing

Found a bug or want to improve the scraper? Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This is a tool for ethical consumption research. Use responsibly and respect the EMH website's terms of service.

---

**Let's help some animals! 🌱**
