"""Filtering logic to identify meat products from FoodRepo data."""

import re
from typing import Dict, List, Set, Optional, Any


class MeatProductFilter:
    """Filter to identify meat products from product data."""

    # Multilingual meat category keywords
    MEAT_CATEGORIES = {
        # German
        'fleisch', 'rindfleisch', 'schweinefleisch', 'kalbfleisch', 'lammfleisch',
        'geflügel', 'poulet', 'huhn', 'ente', 'gans', 'truthahn', 'pute',
        'wurst', 'wurstware', 'aufschnitt', 'speck', 'schinken',
        'hackfleisch', 'gehacktes', 'bratwurst', 'leberwurst',

        # French
        'viande', 'boeuf', 'porc', 'veau', 'agneau', 'mouton',
        'volaille', 'poulet', 'canard', 'oie', 'dinde', 'dindon',
        'charcuterie', 'jambon', 'saucisse', 'saucisson', 'pâté',
        'bacon', 'lard', 'rôti', 'escalope', 'côtelette',

        # Italian
        'carne', 'manzo', 'maiale', 'vitello', 'agnello', 'montone',
        'pollame', 'pollo', 'anatra', 'oca', 'tacchino',
        'salumi', 'prosciutto', 'salame', 'salsiccia', 'pancetta',
        'braciola', 'scaloppina', 'bistecca',

        # English (for international products)
        'meat', 'beef', 'pork', 'veal', 'lamb', 'mutton',
        'poultry', 'chicken', 'duck', 'goose', 'turkey',
        'sausage', 'ham', 'bacon', 'salami', 'pepperoni',
        'steak', 'chops', 'ground', 'minced'
    }

    # Ingredient keywords for meat detection
    MEAT_INGREDIENTS = {
        # Specific animals
        'rind', 'schwein', 'kalb', 'lamm', 'ziege', 'kaninchen',
        'hirsch', 'reh', 'wildschwein', 'bison',  # Game meats
        'boeuf', 'porc', 'veau', 'agneau', 'chèvre', 'lapin',
        'cerf', 'chevreuil', 'sanglier',
        'manzo', 'maiale', 'vitello', 'agnello', 'capra', 'coniglio',
        'cervo', 'capriolo', 'cinghiale',
        'beef', 'pork', 'veal', 'lamb', 'goat', 'rabbit',
        'venison', 'deer', 'boar', 'bison',

        # Poultry
        'huhn', 'hähnchen', 'hühnchen', 'ente', 'gans', 'truthahn', 'pute',
        'poulet', 'canard', 'oie', 'dinde', 'dindon', 'caille',
        'pollo', 'anatra', 'oca', 'tacchino', 'quaglia',
        'chicken', 'duck', 'goose', 'turkey', 'quail', 'fowl',

        # Fish and seafood
        'fisch', 'lachs', 'forelle', 'thunfisch', 'kabeljau', 'hecht',
        'garnele', 'krabbe', 'hummer', 'muschel', 'tintenfisch',
        'poisson', 'saumon', 'truite', 'thon', 'cabillaud', 'brochet',
        'crevette', 'crabe', 'homard', 'moule', 'calmar',
        'pesce', 'salmone', 'trota', 'tonno', 'merluzzo', 'luccio',
        'gambero', 'granchio', 'aragosta', 'cozza', 'calamaro',
        'fish', 'salmon', 'trout', 'tuna', 'cod', 'pike',
        'shrimp', 'prawn', 'crab', 'lobster', 'mussel', 'squid', 'octopus',

        # Processed meats
        'wurst', 'schinken', 'speck', 'leberwurst', 'blutwurst',
        'saucisse', 'jambon', 'lard', 'boudin', 'pâté', 'rillettes',
        'salsiccia', 'prosciutto', 'pancetta', 'mortadella', 'salame',
        'sausage', 'ham', 'bacon', 'salami', 'pepperoni', 'chorizo'
    }

    # Non-meat exclusions (to avoid false positives)
    EXCLUSIONS = {
        'vegetarisch', 'vegan', 'pflanzlich', 'tofu', 'seitan',
        'végétarien', 'végétalien', 'végétal', 'soja',
        'vegetariano', 'vegano', 'vegetale', 'soia',
        'vegetarian', 'vegan', 'plant-based', 'soy', 'soya'
    }

    def __init__(self):
        """Initialize filter with compiled regex patterns."""
        # Compile patterns for better performance
        self.meat_category_pattern = re.compile(
            r'\b(' + '|'.join(self.MEAT_CATEGORIES) + r')\b',
            re.IGNORECASE
        )

        self.meat_ingredient_pattern = re.compile(
            r'\b(' + '|'.join(self.MEAT_INGREDIENTS) + r')\b',
            re.IGNORECASE
        )

        self.exclusion_pattern = re.compile(
            r'\b(' + '|'.join(self.EXCLUSIONS) + r')\b',
            re.IGNORECASE
        )

    def is_meat_product(self, product: Dict[str, Any]) -> bool:
        """Check if a product is likely a meat product.

        Args:
            product: Product dictionary with name, categories, ingredients_text, etc.

        Returns:
            True if product appears to be meat-based
        """
        # Check for exclusions first
        if self._has_exclusions(product):
            return False

        # Check categories
        if self._has_meat_categories(product):
            return True

        # Check ingredients
        if self._has_meat_ingredients(product):
            return True

        # Check product name
        if self._has_meat_in_name(product):
            return True

        return False

    def _has_exclusions(self, product: Dict[str, Any]) -> bool:
        """Check if product has vegetarian/vegan exclusions."""
        # Note: FoodRepo v3 API does not provide brands or categories
        text_fields = [
            product.get('name', ''),
            product.get('ingredients_text', ''),
        ]

        full_text = ' '.join(str(field) for field in text_fields if field)
        return bool(self.exclusion_pattern.search(full_text))

    def _has_meat_categories(self, product: Dict[str, Any]) -> bool:
        """Check if product categories indicate meat."""
        categories = product.get('categories', '')
        if not categories:
            return False

        return bool(self.meat_category_pattern.search(str(categories)))

    def _has_meat_ingredients(self, product: Dict[str, Any]) -> bool:
        """Check if ingredients contain meat."""
        ingredients = product.get('ingredients_text', '')
        if not ingredients:
            return False

        return bool(self.meat_ingredient_pattern.search(str(ingredients)))

    def _has_meat_in_name(self, product: Dict[str, Any]) -> bool:
        """Check if product name contains meat terms."""
        name = product.get('name', '')
        if not name:
            return False

        # Check both category and ingredient patterns in name
        return bool(
            self.meat_category_pattern.search(str(name)) or
            self.meat_ingredient_pattern.search(str(name))
        )

    def filter_meat_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter list of products to only include meat products.

        Args:
            products: List of product dictionaries

        Returns:
            Filtered list containing only meat products
        """
        meat_products = []

        print(f"Filtering {len(products)} products for meat products...")

        for product in products:
            if self.is_meat_product(product):
                meat_products.append(product)

        print(f"Found {len(meat_products)} meat products ({len(meat_products)/len(products)*100:.1f}%)")
        return meat_products

    def get_filter_stats(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about filtering results.

        Args:
            products: List of product dictionaries

        Returns:
            Dictionary with filtering statistics
        """
        stats = {
            'total': len(products),
            'meat': 0,
            'excluded': 0,
            'by_category': 0,
            'by_ingredient': 0,
            'by_name': 0
        }

        for product in products:
            if self._has_exclusions(product):
                stats['excluded'] += 1
                continue

            is_meat = False

            if self._has_meat_categories(product):
                stats['by_category'] += 1
                is_meat = True

            if self._has_meat_ingredients(product):
                stats['by_ingredient'] += 1
                is_meat = True

            if self._has_meat_in_name(product):
                stats['by_name'] += 1
                is_meat = True

            if is_meat:
                stats['meat'] += 1

        return stats