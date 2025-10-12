"""Rating lookup and mapping utilities for EMH data."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re


class EMHRatingMapper:
    """Maps animal-label pairs to EMH welfare ratings."""

    def __init__(self, emh_csv_path: Optional[Path] = None):
        """Initialize mapper with EMH ratings data.

        Args:
            emh_csv_path: Path to EMH ratings CSV file. If None, uses default location.
        """
        if emh_csv_path is None:
            emh_csv_path = Path(__file__).parent.parent / "emh_ratings.csv"

        self.emh_csv_path = emh_csv_path
        self.ratings_map = {}
        self.label_normalizations = {}
        self.animal_normalizations = {}
        self._load_ratings()
        self._build_normalizations()

    def _load_ratings(self):
        """Load EMH ratings from CSV file."""
        if not self.emh_csv_path.exists():
            print(f"Warning: EMH ratings file not found: {self.emh_csv_path}")
            return

        try:
            with self.emh_csv_path.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    label = row['label'].strip()
                    animal = row['animal'].strip()
                    tier = row['tier'].strip()
                    steps_to_go = int(row['steps_to_go']) if row['steps_to_go'].strip().isdigit() else None

                    # Skip rows with empty animal (like milk entries without animal)
                    if not animal:
                        continue

                    key = (label.lower(), animal.lower())
                    self.ratings_map[key] = {
                        'tier': tier,
                        'steps_to_go': steps_to_go,
                        'label': label,
                        'animal': animal,
                        'product_title': row.get('product_title', ''),
                        'product_url': row.get('product_url', ''),
                        'label_url': row.get('label_url', '')
                    }

            print(f"Loaded {len(self.ratings_map)} EMH ratings from {self.emh_csv_path}")

        except Exception as e:
            print(f"Error loading EMH ratings: {e}")

    def _build_normalizations(self):
        """Build normalization mappings for labels and animals."""

        # Animal normalization - now classifier outputs EMH terms directly
        # Just keep EMH terms as-is
        self.animal_normalizations = {
            # EMH animals as-is
            'rindfleisch': 'rindfleisch',
            'schweinefleisch': 'schweinefleisch',
            'kalbfleisch': 'kalbfleisch',
            'poulet': 'poulet',
            'eier': 'eier',
            'milch': 'milch',

            # Handle some variations
            'pouletfleisch': 'poulet',
            'beef': 'rindfleisch',
            'pork': 'schweinefleisch',
            'veal': 'kalbfleisch',
            'chicken': 'poulet',
            'eggs': 'eier',
            'milk': 'milch'
        }

        # Label normalization - now classifier outputs EMH labels directly
        # Just keep EMH labels as-is
        self.label_normalizations = {}

        # Extract unique labels from EMH data and map them to themselves
        emh_labels = set()
        for (label, _) in self.ratings_map.keys():
            emh_labels.add(label)

        # Map EMH labels to themselves (no normalization needed)
        for emh_label in emh_labels:
            self.label_normalizations[emh_label.lower()] = emh_label

        # Add some common input variations that might come from products
        # Map variations to exact EMH labels
        variation_mappings = {
            'natura-beef': 'NATURA-BEEF D',
            'natura beef': 'NATURA-BEEF D',
            'naturabeef': 'NATURA-BEEF D',
            'natura-veal': 'NATURA-VEAL DE',
            'natura veal': 'NATURA-VEAL DE',
            'naturaveal': 'NATURA-VEAL DE',
            'migros weide-beef': 'MIGROS WEIDE-BEEF D',
            'weide-beef': 'MIGROS WEIDE-BEEF D',
            'bio suisse': 'BIO SUISSE / BIO KNOSPE D',
            'knospe': 'BIO SUISSE / BIO KNOSPE D',
            'bio knospe': 'BIO SUISSE / BIO KNOSPE D',
            'coop naturafarm': 'COOP NATURAFARM D',
            'coop naturaplan': 'COOP NATURAPLAN D',
            'ip-suisse': 'IP-SUISSE D',
            'suisse garantie': 'SUISSE GARANTIE D',
            'agri natura': 'AGRI NATURA D',
            'demeter': 'DEMETER D'
        }

        for variation, emh_label in variation_mappings.items():
            self.label_normalizations[variation.lower()] = emh_label

    def _normalize_label_text(self, text: str) -> str:
        """Normalize label text for comparison."""
        if not text:
            return ''

        # Convert to lowercase
        normalized = text.lower().strip()

        # Remove common suffixes
        normalized = re.sub(r'\s+d$', '', normalized)  # Remove " D" suffix

        # Normalize spacing and punctuation
        normalized = re.sub(r'[_\-/]+', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def normalize_animal(self, animal: str) -> str:
        """Normalize animal name for lookup.

        Args:
            animal: Animal name from classifier

        Returns:
            Normalized animal name for EMH lookup
        """
        if not animal:
            return 'unknown'

        normalized = animal.lower().strip()
        return self.animal_normalizations.get(normalized, normalized)

    def normalize_label(self, label: str) -> Optional[str]:
        """Normalize label name for lookup.

        Args:
            label: Label name from classifier

        Returns:
            Normalized label name for EMH lookup, or None if no match
        """
        if not label or label.lower() == 'unknown':
            return None

        # Direct match (case insensitive)
        label_lower = label.lower()
        if label_lower in self.label_normalizations:
            return self.label_normalizations[label_lower]

        # If classifier already outputs exact EMH label, return as-is
        if label in [v for v in self.label_normalizations.values()]:
            return label

        return None

    def get_rating(self, animal: str, label: str) -> Optional[Dict[str, Any]]:
        """Get EMH rating for animal-label pair.

        Args:
            animal: Animal type (from classifier)
            label: Label/program name (from classifier)

        Returns:
            EMH rating dictionary or None if not found
        """
        # Normalize inputs
        norm_animal = self.normalize_animal(animal)
        norm_label = self.normalize_label(label)

        if not norm_label:
            return None

        # Look up rating
        key = (norm_label.lower(), norm_animal.lower())
        return self.ratings_map.get(key)

    def get_all_ratings_for_label(self, label: str) -> List[Dict[str, Any]]:
        """Get all ratings for a specific label across all animals.

        Args:
            label: Label/program name

        Returns:
            List of rating dictionaries
        """
        norm_label = self.normalize_label(label)
        if not norm_label:
            return []

        ratings = []
        for (emh_label, emh_animal), rating_data in self.ratings_map.items():
            if emh_label.lower() == norm_label.lower():
                ratings.append(rating_data)

        return ratings

    def get_all_ratings_for_animal(self, animal: str) -> List[Dict[str, Any]]:
        """Get all ratings for a specific animal across all labels.

        Args:
            animal: Animal type

        Returns:
            List of rating dictionaries
        """
        norm_animal = self.normalize_animal(animal)

        ratings = []
        for (emh_label, emh_animal), rating_data in self.ratings_map.items():
            if emh_animal.lower() == norm_animal.lower():
                ratings.append(rating_data)

        return ratings

    def map_products_to_ratings(self, classified_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map classified products to EMH ratings.

        Args:
            classified_products: List of products with classification results

        Returns:
            List of products with EMH rating information added
        """
        print(f"Mapping {len(classified_products)} products to EMH ratings...")

        mapped_products = []
        stats = {
            'mapped': 0,
            'no_label': 0,
            'no_rating': 0,
            'by_tier': {'TOP': 0, 'OK': 0, 'UNCOOL': 0, 'NO GO': 0}
        }

        for product in classified_products:
            mapped_product = product.copy()

            animal = product.get('classified_animal', 'unknown')
            label = product.get('classified_label', 'unknown')

            if label == 'unknown':
                stats['no_label'] += 1
                mapped_product['emh_tier'] = None
                mapped_product['emh_steps_to_go'] = None
                mapped_product['emh_mapping_status'] = 'no_label'
            else:
                rating = self.get_rating(animal, label)

                if rating:
                    mapped_product['emh_tier'] = rating['tier']
                    mapped_product['emh_steps_to_go'] = rating['steps_to_go']
                    mapped_product['emh_mapping_status'] = 'mapped'
                    mapped_product['emh_label'] = rating['label']
                    mapped_product['emh_animal'] = rating['animal']

                    stats['mapped'] += 1
                    if rating['tier'] in stats['by_tier']:
                        stats['by_tier'][rating['tier']] += 1
                else:
                    mapped_product['emh_tier'] = None
                    mapped_product['emh_steps_to_go'] = None
                    mapped_product['emh_mapping_status'] = 'no_rating'
                    stats['no_rating'] += 1

            mapped_products.append(mapped_product)

        print(f"EMH mapping complete:")
        print(f"  Mapped to ratings: {stats['mapped']}")
        print(f"  No label identified: {stats['no_label']}")
        print(f"  Label but no rating: {stats['no_rating']}")
        print(f"  By tier: {stats['by_tier']}")

        return mapped_products

    def get_mapping_stats(self) -> Dict[str, Any]:
        """Get statistics about the EMH ratings data.

        Returns:
            Dictionary with statistics
        """
        if not self.ratings_map:
            return {}

        stats = {
            'total_ratings': len(self.ratings_map),
            'unique_labels': len(set(label for label, _ in self.ratings_map.keys())),
            'unique_animals': len(set(animal for _, animal in self.ratings_map.keys())),
            'by_tier': {},
            'by_animal': {},
            'by_label': {}
        }

        for rating_data in self.ratings_map.values():
            tier = rating_data['tier']
            animal = rating_data['animal']
            label = rating_data['label']

            stats['by_tier'][tier] = stats['by_tier'].get(tier, 0) + 1
            stats['by_animal'][animal] = stats['by_animal'].get(animal, 0) + 1
            stats['by_label'][label] = stats['by_label'].get(label, 0) + 1

        return stats