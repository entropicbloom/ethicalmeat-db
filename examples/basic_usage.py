#!/usr/bin/env python3
"""
Basic usage example for the ethical meat scraper.
This demonstrates how to use the EMHScraper class programmatically.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraper import EMHScraper


def main():
    """Demonstrate basic usage of the scraper."""

    # Initialize scraper with custom settings
    scraper = EMHScraper(
        cache_dir=Path("cache"),  # Enable caching
        rate_limit=1.0  # 1 second between requests
    )

    print("Example 1: Discover all label URLs")
    print("=" * 60)
    label_urls = scraper.discover_label_urls()
    print(f"Found {len(label_urls)} labels:")
    for url in label_urls[:5]:  # Show first 5
        print(f"  - {url}")
    print()

    print("Example 2: Parse a specific label page")
    print("=" * 60)
    if label_urls:
        first_label = label_urls[0]
        result = scraper.parse_label_page(first_label)
        print(f"Label: {result['label_title']}")
        print(f"URL: {result['label_url']}")
        print(f"Products found: {len(result['products'])}")

        if result['products']:
            print("\nFirst product:")
            p = result['products'][0]
            print(f"  Animal: {p['animal']}")
            print(f"  Text: {p['animal_text']}")
            print(f"  URL: {p['url']}")
    print()

    print("Example 3: Parse a product page")
    print("=" * 60)
    if label_urls:
        result = scraper.parse_label_page(label_urls[0])
        if result['products']:
            product_url = result['products'][0]['url']
            product_data = scraper.parse_product_page(product_url)

            print(f"Title: {product_data['title']}")
            print(f"Animal: {product_data['animal']}")
            print(f"Tier: {product_data['tier']}")
            print(f"Steps to TOP: {product_data['steps_to_go']}")
    print()

    print("Example 4: Harvest all ratings (this may take a while)")
    print("=" * 60)
    print("Note: Uncomment the code below to run a full harvest")
    print()
    # Uncomment to run full harvest:
    # all_data = scraper.harvest_all_ratings()
    # print(f"Total products scraped: {len(all_data)}")
    #
    # # Count by tier
    # tier_counts = {}
    # for item in all_data:
    #     tier = item.get('tier', 'UNKNOWN')
    #     tier_counts[tier] = tier_counts.get(tier, 0) + 1
    #
    # print("\nBreakdown by tier:")
    # for tier, count in sorted(tier_counts.items()):
    #     print(f"  {tier}: {count}")


if __name__ == "__main__":
    main()
