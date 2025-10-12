# Ethical Meat Database 🐄🐷🐔

A comprehensive tool for mapping product barcodes to animal welfare ratings, combining data from [FoodRepo](https://foodrepo.org) and [Essen mit Herz](https://essenmitherz.ch) (EMH).

## What It Does

**📊 Complete Pipeline**: Barcode → Product → Animal/Label → Welfare Rating

1. **FoodRepo Integration**: Fetches Swiss product data with barcodes, names, brands, categories, and ingredients
2. **Meat Detection**: Filters products to identify meat and animal products using multilingual keywords
3. **Smart Classification**: Uses regex rules + LLM integration to classify animal types and Swiss labels
4. **EMH Mapping**: Maps products to welfare ratings (TOP, OK, UNCOOL, NO GO) from Essen mit Herz
5. **Complete Output**: Generates barcode → welfare rating lookup tables

**🎯 End Result**: Know the animal welfare rating of any Swiss meat product by scanning its barcode!

## Features

**EMH Scraping (Original)**:
- 🔍 **Robust parsing** with CSS selectors + regex fallbacks
- 💾 **Smart caching** to avoid repeated requests
- ⏱️ **Rate limiting** to be respectful to the server

**FoodRepo Integration (New)**:
- 🔗 **FoodRepo API** integration with authentication and pagination
- 🥩 **Multilingual meat detection** (German, French, Italian, English)
- 🤖 **Smart classification** using regex rules + LLM fallback
- 🗺️ **Label normalization** for Swiss meat programs and retailers

**Output & Pipeline**:
- 📊 **Multiple formats** (JSON, CSV, barcode mappings)
- 🚀 **Complete pipeline** orchestration
- 📋 **Detailed logging** and progress tracking
- 🎯 **Clean CLI interfaces**

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your FoodRepo API key (get one free at [foodrepo.org](https://foodrepo.org)):

```bash
echo "FOOD_REPO_API_KEY=your_api_key_here" > .env
```

## Usage

### 🚀 Full Pipeline (Recommended)

Create complete barcode → welfare rating mappings:

```bash
# Test with small sample
python pipeline.py --limit 100

# Full pipeline
python pipeline.py --output my_barcode_mappings
```

This will:
1. Fetch products from FoodRepo API
2. Filter to meat products using multilingual detection
3. Classify animal types and Swiss labels
4. Map to EMH welfare ratings
5. Generate barcode lookup tables

### 📊 EMH Scraping Only

If you only want EMH welfare ratings (original functionality):

```bash
python -m emh.cli
```

This will:
- Scrape all labels and their animal products from EMH
- Save results to `emh_ratings.json` and `emh_ratings.csv`
- Show a summary of the findings

### 🔧 Pipeline Options

```bash
# Custom output filename
python pipeline.py --output my_mappings

# Small test run
python pipeline.py --limit 500

# Disable caching (always fetch fresh from FoodRepo)
python pipeline.py --no-cache

# Custom cache directory
python pipeline.py --cache-dir my_foodrepo_cache

# Slower API rate limit
python pipeline.py --rate-limit 0.5

# Skip regex rules, use only LLM classification
python pipeline.py --no-rules
```

### 📊 EMH-Only Options

```bash
# Save to custom filename
python -m emh.cli --output my_ratings

# Only JSON output
python -m emh.cli --format json

# Disable caching (always fetch fresh)
python -m emh.cli --no-cache

# Slower rate limit (2 seconds between requests)
python -m emh.cli --rate-limit 2.0
```

### Help

```bash
# Full pipeline help
python pipeline.py --help

# EMH scraper help
python -m emh.cli --help

# Test components
python test_foodrepo.py
```

## Output Formats

### 🚀 Pipeline Output

**Main results** (`barcode_welfare_mappings.json`):
```json
[
  {
    "barcode": "7610200111111",
    "name": "Bio Poulet Schweiz",
    "brands": ["Migros Bio"],
    "classified_animal": "chicken",
    "classified_label": "migros naturafarm",
    "emh_tier": "TOP",
    "emh_steps_to_go": 8,
    "classification_confidence": 0.9
  }
]
```

**Barcode mappings** (`barcode_welfare_mappings_mappings.csv`):
```csv
barcode,product_name,animal,label,welfare_tier,steps_to_go
7610200111111,Bio Poulet Schweiz,chicken,migros naturafarm,TOP,8
7610200222222,Natura-Beef Entrecôte,beef,natura-beef,TOP,8
```

### 📊 EMH-Only Output

```json
[
  {
    "label": "Label MIGROS WEIDE-BEEF",
    "animal": "rindfleisch",
    "tier": "TOP",
    "steps_to_go": 13,
    "product_title": "Rindfleisch Migros Weide-Beef",
    "product_url": "https://essenmitherz.ch/rindfleisch-migros-weide-beef/",
    "label_url": "https://essenmitherz.ch/label-migros-weide-beef/"
  }
]
```

## Project Structure

```
ethicalmeat-db/
├── emh/                      # EMH website scraping module
│   ├── __init__.py
│   ├── scraper.py            # EMH website scraping logic
│   └── cli.py                # EMH CLI interface
├── foodrepo/                 # FoodRepo API integration module
│   ├── __init__.py
│   ├── client.py             # FoodRepo API client with pagination
│   ├── filters.py            # Multilingual meat product detection
│   └── classifier.py         # Smart animal/label classification
├── utils/                    # Shared utilities
│   ├── __init__.py
│   └── mapping.py            # EMH rating lookup and normalization
├── pipeline.py               # Complete pipeline orchestration
├── test_foodrepo.py          # Integration testing script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API keys)
├── emh_ratings.csv          # EMH welfare ratings database
├── .gitignore
└── README.md                # This file
```

## How It Works

### 🚀 Full Pipeline Process

1. **FoodRepo Data**: Fetches Swiss products via API (barcodes, names, brands, categories, ingredients)
2. **Meat Detection**: Multilingual filtering using category and ingredient keywords
3. **Classification**:
   - **Regex rules**: Fast classification for obvious cases
   - **LLM integration**: Smart classification for complex cases (API not included)
4. **EMH Mapping**: Maps animal/label pairs to welfare ratings using normalization rules
5. **Output Generation**: Creates barcode lookup tables in multiple formats

### 📊 EMH Scraping Process

1. **Discover labels**: Scrapes the [label index page](https://essenmitherz.ch/label-und-marken/) to find all labels
2. **Parse label pages**: For each label, finds the "Produkte:" section with animal-specific links
3. **Extract ratings**: Visits each animal product page and extracts ratings via robust parsing
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
