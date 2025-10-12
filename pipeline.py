#!/usr/bin/env python3
"""Full pipeline orchestration for barcode to welfare rating mapping."""

import argparse
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from foodrepo.client import FoodRepoClient
from foodrepo.filters import MeatProductFilter
from foodrepo.classifier import ProductClassifier
from utils.mapping import EMHRatingMapper


class BarcodeMappingPipeline:
    """Main pipeline for creating barcode to welfare rating mappings."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 0.2,
        cache_dir: Optional[Path] = None,
        use_simple_rules: bool = True
    ):
        """Initialize pipeline components.

        Args:
            api_key: FoodRepo API key
            rate_limit: Rate limit for API requests
            cache_dir: Directory for caching data
            use_simple_rules: Whether to use regex rules before LLM classification
        """
        self.foodrepo_client = FoodRepoClient(api_key=api_key, rate_limit=rate_limit)
        self.meat_filter = MeatProductFilter()
        self.classifier = ProductClassifier(use_simple_rules=use_simple_rules)
        self.emh_mapper = EMHRatingMapper()

        self.cache_dir = cache_dir or Path("foodrepo_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def run_full_pipeline(
        self,
        limit: Optional[int] = None,
        use_cache: bool = True,
        output_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Run the complete pipeline.

        Args:
            limit: Maximum number of products to process
            use_cache: Whether to use cached FoodRepo data
            output_path: Path to save final results

        Returns:
            List of products with barcode to welfare rating mappings
        """
        print("=" * 80)
        print("BARCODE TO WELFARE RATING MAPPING PIPELINE")
        print("=" * 80)

        # Step 1: Fetch products from FoodRepo
        products_cache_path = self.cache_dir / "foodrepo_products.json"

        if use_cache and products_cache_path.exists():
            print(f"\n1. Loading cached FoodRepo products from {products_cache_path}")
            products = self.foodrepo_client.load_products_cache(products_cache_path)
        else:
            print(f"\n1. Fetching products from FoodRepo API (limit: {limit or 'all'})")
            products = self.foodrepo_client.fetch_products(limit=limit)

            if use_cache:
                self.foodrepo_client.save_products_cache(products, products_cache_path)

        if not products:
            print("❌ No products fetched from FoodRepo")
            return []

        # Step 2: Filter to meat products
        print(f"\n2. Filtering for meat products")
        meat_products = self.meat_filter.filter_meat_products(products)

        if not meat_products:
            print("❌ No meat products found after filtering")
            return []

        # Print filter stats
        filter_stats = self.meat_filter.get_filter_stats(products)
        print(f"   Filter stats: {filter_stats}")

        # Step 3: Classify animal types and labels
        print(f"\n3. Classifying animal types and Swiss labels")
        classified_products = self.classifier.classify_products(meat_products)

        # Step 4: Map to EMH ratings
        print(f"\n4. Mapping to EMH welfare ratings")
        final_products = self.emh_mapper.map_products_to_ratings(classified_products)

        # Step 5: Save results
        if output_path:
            print(f"\n5. Saving results to {output_path}")
            self.save_results(final_products, output_path)

        # Print final summary
        self.print_summary(final_products)

        return final_products

    def save_results(self, products: List[Dict[str, Any]], output_path: Path):
        """Save pipeline results in multiple formats.

        Args:
            products: Final product data with mappings
            output_path: Base output path (extensions will be added)
        """
        # Save detailed JSON
        json_path = output_path.with_suffix('.json')
        with json_path.open('w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"   Detailed data: {json_path}")

        # Save CSV with key fields
        csv_path = output_path.with_suffix('.csv')
        self.save_csv_summary(products, csv_path)
        print(f"   Summary CSV: {csv_path}")

        # Save mapping-only CSV (barcode -> rating)
        mapping_path = output_path.parent / f"{output_path.stem}_mappings.csv"
        self.save_mapping_csv(products, mapping_path)
        print(f"   Barcode mappings: {mapping_path}")

    def save_csv_summary(self, products: List[Dict[str, Any]], csv_path: Path):
        """Save summary CSV with key product information."""
        fieldnames = [
            'barcode', 'name', 'brands', 'categories',
            'classified_animal', 'classified_label', 'classification_confidence',
            'emh_tier', 'emh_steps_to_go', 'emh_mapping_status'
        ]

        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for product in products:
                row = {}
                for field in fieldnames:
                    value = product.get(field, '')

                    # Handle list fields
                    if isinstance(value, list):
                        value = '; '.join(str(v) for v in value)

                    row[field] = value

                writer.writerow(row)

    def save_mapping_csv(self, products: List[Dict[str, Any]], csv_path: Path):
        """Save barcode to welfare rating mapping CSV."""
        fieldnames = ['barcode', 'product_name', 'animal', 'label', 'welfare_tier', 'steps_to_go']

        with csv_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for product in products:
                # Only include products with welfare ratings
                if product.get('emh_mapping_status') == 'mapped':
                    writer.writerow({
                        'barcode': product.get('barcode', ''),
                        'product_name': product.get('name', ''),
                        'animal': product.get('classified_animal', ''),
                        'label': product.get('classified_label', ''),
                        'welfare_tier': product.get('emh_tier', ''),
                        'steps_to_go': product.get('emh_steps_to_go', '')
                    })

    def print_summary(self, products: List[Dict[str, Any]]):
        """Print pipeline summary statistics."""
        print(f"\n" + "=" * 80)
        print("PIPELINE SUMMARY")
        print("=" * 80)

        total = len(products)
        mapped = len([p for p in products if p.get('emh_mapping_status') == 'mapped'])
        no_label = len([p for p in products if p.get('emh_mapping_status') == 'no_label'])
        no_rating = len([p for p in products if p.get('emh_mapping_status') == 'no_rating'])

        print(f"\nTotal meat products processed: {total}")
        print(f"Successfully mapped to welfare ratings: {mapped} ({mapped/total*100:.1f}%)")
        print(f"No label identified: {no_label} ({no_label/total*100:.1f}%)")
        print(f"Label identified but no rating: {no_rating} ({no_rating/total*100:.1f}%)")

        # Welfare tier distribution
        tier_counts = {}
        for product in products:
            tier = product.get('emh_tier')
            if tier:
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

        if tier_counts:
            print(f"\nWelfare tier distribution:")
            for tier in ['TOP', 'OK', 'UNCOOL', 'NO GO']:
                if tier in tier_counts:
                    print(f"  {tier}: {tier_counts[tier]}")

        # Most common animals
        animal_counts = {}
        for product in products:
            animal = product.get('classified_animal')
            if animal and animal != 'unknown':
                animal_counts[animal] = animal_counts.get(animal, 0) + 1

        if animal_counts:
            print(f"\nMost common animals:")
            sorted_animals = sorted(animal_counts.items(), key=lambda x: x[1], reverse=True)
            for animal, count in sorted_animals[:5]:
                print(f"  {animal}: {count}")

        # Most common labels
        label_counts = {}
        for product in products:
            label = product.get('classified_label')
            if label and label != 'unknown':
                label_counts[label] = label_counts.get(label, 0) + 1

        if label_counts:
            print(f"\nMost common labels:")
            sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
            for label, count in sorted_labels[:5]:
                print(f"  {label}: {count}")

        print(f"\n🎯 Ready to use! You now have barcode → welfare rating mappings.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create barcode to welfare rating mappings using FoodRepo + EMH data"
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Limit number of products to process (for testing)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='barcode_welfare_mappings',
        help='Output filename base (default: barcode_welfare_mappings)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable FoodRepo API caching'
    )

    parser.add_argument(
        '--cache-dir',
        type=str,
        default='foodrepo_cache',
        help='Directory for caching (default: foodrepo_cache)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.2,
        help='Seconds between FoodRepo API requests (default: 0.2)'
    )

    parser.add_argument(
        '--no-rules',
        action='store_true',
        help='Skip regex rules, use only LLM classification'
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        pipeline = BarcodeMappingPipeline(
            rate_limit=args.rate_limit,
            cache_dir=Path(args.cache_dir),
            use_simple_rules=not args.no_rules
        )

        # Run pipeline
        output_path = Path(args.output)
        results = pipeline.run_full_pipeline(
            limit=args.limit,
            use_cache=not args.no_cache,
            output_path=output_path
        )

        if not results:
            print("\n❌ Pipeline completed but no results generated")
            sys.exit(1)

        print(f"\n✨ Pipeline completed successfully!")
        print(f"📊 Results saved with base name: {args.output}")

        # Attribution notice
        print(f"\n" + "=" * 80)
        print("DATA ATTRIBUTION")
        print("=" * 80)
        print("FoodRepo data: CC-BY-4.0 license")
        print("Please include attribution: 'Data from FoodRepo (foodrepo.org), CC-BY-4.0'")
        print("EMH ratings: Essen mit Herz (essenmitherz.ch)")

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()