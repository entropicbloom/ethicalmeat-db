#!/usr/bin/env python3
"""CLI for EMH scraper."""

import argparse
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

from scraper import EMHScraper


def save_json(data: List[Dict[str, Any]], output_path: Path):
    """Save data as JSON."""
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON to: {output_path}")


def save_csv(data: List[Dict[str, Any]], output_path: Path):
    """Save data as CSV."""
    if not data:
        print("No data to save")
        return

    fieldnames = ["label", "animal", "tier", "steps_to_go", "product_title", "product_url", "label_url"]

    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, '') for k in fieldnames})

    print(f"Saved CSV to: {output_path}")


def print_summary(data: List[Dict[str, Any]]):
    """Print a summary of the scraped data."""
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    # Count by tier
    tier_counts = {}
    for item in data:
        tier = item.get('tier', 'UNKNOWN')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print(f"\nTotal products: {len(data)}")
    print("\nBy tier:")
    for tier in ['TOP', 'OK', 'UNCOOL', 'NO GO', 'UNKNOWN']:
        if tier in tier_counts:
            print(f"  {tier}: {tier_counts[tier]}")

    # Count by animal
    animal_counts = {}
    for item in data:
        animal = item.get('animal') or 'unknown'
        animal_counts[animal] = animal_counts.get(animal, 0) + 1

    print("\nBy animal:")
    for animal, count in sorted(animal_counts.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {animal}: {count}")

    # Show some examples
    print("\nExample entries:")
    for item in data[:3]:
        print(f"\n  Label: {item.get('label')}")
        print(f"  Animal: {item.get('animal')}")
        print(f"  Rating: {item.get('tier')} ({item.get('steps_to_go')} steps to go)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape animal welfare ratings from Essen mit Herz website"
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='emh_ratings',
        help='Output filename (without extension, default: emh_ratings)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        default='cache',
        help='Directory for caching HTML (default: cache)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Seconds between requests (default: 1.0)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching'
    )

    args = parser.parse_args()

    # Setup scraper
    cache_dir = None if args.no_cache else Path(args.cache_dir)
    scraper = EMHScraper(cache_dir=cache_dir, rate_limit=args.rate_limit)

    # Scrape data
    print("Starting scrape of Essen mit Herz website...")
    print(f"Cache: {'disabled' if args.no_cache else args.cache_dir}")
    print(f"Rate limit: {args.rate_limit}s between requests\n")

    try:
        data = scraper.harvest_all_ratings()
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during scraping: {e}")
        sys.exit(1)

    if not data:
        print("\nNo data collected!")
        sys.exit(1)

    # Save data
    if args.format in ['json', 'both']:
        save_json(data, Path(f"{args.output}.json"))

    if args.format in ['csv', 'both']:
        save_csv(data, Path(f"{args.output}.csv"))

    # Print summary
    print_summary(data)

    print("\n✨ Done! Let's help some animals! 🐄🐷🐔")


if __name__ == "__main__":
    main()
