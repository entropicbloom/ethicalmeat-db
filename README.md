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

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python src/cli.py
```

This will:
- Scrape all labels and their animal products from EMH
- Save results to `emh_ratings.json` and `emh_ratings.csv`
- Show a summary of the findings

### Advanced Options

```bash
# Save to custom filename
python src/cli.py --output my_ratings

# Only JSON output
python src/cli.py --format json

# Only CSV output
python src/cli.py --format csv

# Disable caching (always fetch fresh)
python src/cli.py --no-cache

# Custom cache directory
python src/cli.py --cache-dir my_cache

# Slower rate limit (2 seconds between requests)
python src/cli.py --rate-limit 2.0
```

### Help

```bash
python src/cli.py --help
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
ethicalmeat/
├── src/
│   ├── __init__.py       # Package init
│   ├── scraper.py        # Core scraping logic
│   └── cli.py            # Command-line interface
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md            # This file
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

## Contributing

Found a bug or want to improve the scraper? Contributions welcome!

## License

This is a tool for ethical consumption research. Use responsibly and respect the EMH website's terms of service.

---

**Let's help some animals! 🌱**
