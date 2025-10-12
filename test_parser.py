#!/usr/bin/env python3
"""Quick test script to verify parsing works with cached data."""

import sys
import hashlib
from pathlib import Path

# Add emh to path
sys.path.insert(0, str(Path(__file__).parent / "emh"))

from scraper import EMHScraper

def test_nature_suisse():
    """Test parsing the Nature Suisse label page."""
    scraper = EMHScraper(cache_dir=Path("cache"), rate_limit=0)

    url = "https://essenmitherz.ch/label-nature-suisse/"
    print(f"Testing: {url}\n")

    result = scraper.parse_label_page(url)

    print(f"Label: {result['label_title']}")
    print(f"Products found: {len(result['products'])}\n")

    if result['products']:
        print("Products:")
        for p in result['products']:
            print(f"  - {p['animal_text']}")
            print(f"    Animal: {p['animal']}")
            print(f"    URL: {p['url']}\n")

        # Test parsing one product page
        first_product = result['products'][0]
        print(f"\nTesting product page: {first_product['url']}")
        product_result = scraper.parse_product_page(first_product['url'])

        print(f"  Title: {product_result['title']}")
        print(f"  Animal: {product_result['animal']}")
        print(f"  Tier: {product_result['tier']}")
        print(f"  Steps: {product_result['steps_to_go']}")
    else:
        print("❌ No products found!")
        return False

    return True

if __name__ == "__main__":
    success = test_nature_suisse()
    sys.exit(0 if success else 1)
