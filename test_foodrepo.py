#!/usr/bin/env python3
"""Test script for FoodRepo integration components."""

import os
import sys
from pathlib import Path

# Test imports
try:
    from foodrepo.client import FoodRepoClient
    from foodrepo.filters import MeatProductFilter
    from foodrepo.classifier import ProductClassifier
    from utils.mapping import EMHRatingMapper
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_components():
    """Test individual components."""
    print("\n" + "="*50)
    print("TESTING COMPONENTS")
    print("="*50)

    # Test EMH mapper
    print("\n1. Testing EMH Rating Mapper...")
    mapper = EMHRatingMapper()
    stats = mapper.get_mapping_stats()
    print(f"   Loaded {stats.get('total_ratings', 0)} ratings")
    print(f"   Labels: {stats.get('unique_labels', 0)}, Animals: {stats.get('unique_animals', 0)}")

    # Test animal normalization
    test_animals = ['rindfleisch', 'schweinefleisch', 'poulet', 'beef', 'unknown']
    print(f"   Animal normalization test:")
    for animal in test_animals:
        normalized = mapper.normalize_animal(animal)
        print(f"     {animal} -> {normalized}")

    # Test label normalization
    test_labels = ['natura-beef', 'bio suisse', 'unknown', 'migros weide-beef']
    print(f"   Label normalization test:")
    for label in test_labels:
        normalized = mapper.normalize_label(label)
        print(f"     {label} -> {normalized}")

    # Test meat filter
    print("\n2. Testing Meat Filter...")
    meat_filter = MeatProductFilter()

    test_products = [
        {
            'name': 'Bio Poulet Schweiz',
            'categories': 'fleisch poulet',
            'ingredients_text': 'Pouletfleisch',
            'brands': ['Bio']
        },
        {
            'name': 'Vegetarian Tofu',
            'categories': 'vegetarian protein',
            'ingredients_text': 'Tofu, vegetables',
            'brands': ['Veggie']
        },
        {
            'name': 'Rindfleisch Natura-Beef',
            'categories': 'meat beef',
            'ingredients_text': 'Beef',
            'brands': ['Natura']
        }
    ]

    meat_products = meat_filter.filter_meat_products(test_products)
    print(f"   Found {len(meat_products)} meat products out of {len(test_products)}")

    # Test classifier
    print("\n3. Testing Product Classifier...")
    classifier = ProductClassifier(use_simple_rules=True)

    for product in meat_products:
        result = classifier.classify_product(product)
        print(f"   Product: {product['name']}")
        print(f"     Animal: {result.animal} (confidence: {result.confidence})")
        print(f"     Label: {result.label}")

    # Test API client initialization (without making requests)
    print("\n4. Testing FoodRepo Client...")
    try:
        client = FoodRepoClient()
        print(f"   ✅ Client initialized (API key configured: {'Yes' if client.api_key else 'No'})")
    except ValueError as e:
        print(f"   ⚠️  Client initialization: {e}")
        print(f"   (This is expected if FOOD_REPO_API_KEY is not set)")

    print(f"\n✅ Component testing complete!")

def show_usage():
    """Show usage examples."""
    print("\n" + "="*50)
    print("USAGE EXAMPLES")
    print("="*50)

    print(f"\n1. Run EMH scraper (existing functionality):")
    print(f"   python -m emh.cli")

    print(f"\n2. Test FoodRepo pipeline (small sample):")
    print(f"   python pipeline.py --limit 100")

    print(f"\n3. Run full pipeline:")
    print(f"   python pipeline.py --output my_mappings")

    print(f"\n4. Pipeline with custom settings:")
    print(f"   python pipeline.py --limit 500 --no-cache --rate-limit 0.5")

    print(f"\nNote: Set FOOD_REPO_API_KEY environment variable to use FoodRepo API")

if __name__ == "__main__":
    test_components()
    show_usage()