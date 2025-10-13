"""Open Food Facts API client for enriching product data with brands."""

import time
import subprocess
import json
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class OpenFoodFactsClient:
    """Client for accessing Open Food Facts API to get brand information."""

    BASE_URL = "https://world.openfoodfacts.org/api/v2"

    def __init__(self, rate_limit: float = 0.6):
        """Initialize client with rate limiting.

        Args:
            rate_limit: Seconds to wait between requests (default: 0.6s = 100 req/min)
        """
        self.rate_limit = rate_limit
        self.cache = {}  # In-memory cache for already fetched products

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make request to Open Food Facts API using curl.

        Args:
            url: Full URL to request

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: On API errors
        """
        if self.rate_limit > 0:
            time.sleep(self.rate_limit)

        curl_command = [
            "curl",
            "-sS",
            url,
            "-H", "Accept: application/json",
            "-H", "User-Agent: ethicalmeat-db/0.1 (ethical.meat@example.com)",
        ]

        result = subprocess.run(curl_command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Open Food Facts API request failed: {result.stderr}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Open Food Facts response: {e}")

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Get product information by barcode.

        Args:
            barcode: Product barcode

        Returns:
            Product data with brands/categories or None if not found
        """
        # Check cache first
        if barcode in self.cache:
            return self.cache[barcode]

        url = f"{self.BASE_URL}/product/{barcode}"

        try:
            data = self._make_request(url)

            # Check if product was found
            if data.get("status") != 1:
                self.cache[barcode] = None
                return None

            product = data.get("product", {})

            # Extract relevant fields
            result = {
                "barcode": barcode,
                "brands": product.get("brands", ""),
                "brands_tags": product.get("brands_tags", []),
                "categories": product.get("categories", ""),
                "categories_tags": product.get("categories_tags", []),
            }

            self.cache[barcode] = result
            return result

        except RuntimeError:
            # API error - cache as None to avoid repeated failures
            self.cache[barcode] = None
            return None

    def enrich_products_with_brands(
        self,
        products: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """Enrich FoodRepo products with brand information from Open Food Facts.

        Args:
            products: List of FoodRepo product dictionaries
            show_progress: Whether to show progress updates

        Returns:
            List of enriched products with brand information added
        """
        enriched_products = []
        found_count = 0
        not_found_count = 0

        if show_progress:
            print(f"Enriching {len(products)} products with Open Food Facts brand data...")

        for i, product in enumerate(products):
            barcode = product.get("barcode")

            if show_progress and (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(products)} ({found_count} enriched, {not_found_count} not found)")

            if not barcode:
                enriched_products.append(product)
                continue

            # Get brand info from Open Food Facts
            off_data = self.get_product_by_barcode(barcode)

            enriched_product = product.copy()

            if off_data and off_data.get("brands"):
                # Add brand information
                enriched_product["brands"] = off_data["brands"]
                enriched_product["brands_tags"] = off_data.get("brands_tags", [])
                enriched_product["off_categories"] = off_data.get("categories", "")
                enriched_product["off_categories_tags"] = off_data.get("categories_tags", [])
                enriched_product["brand_source"] = "openfoodfacts"
                found_count += 1
            else:
                # No brand info found
                enriched_product["brands"] = ""
                enriched_product["brands_tags"] = []
                enriched_product["brand_source"] = "none"
                not_found_count += 1

            enriched_products.append(enriched_product)

        if show_progress:
            print(f"Enrichment complete:")
            print(f"  Found brands: {found_count}/{len(products)} ({found_count/len(products)*100:.1f}%)")
            print(f"  Not found: {not_found_count}/{len(products)} ({not_found_count/len(products)*100:.1f}%)")

        return enriched_products

    def search_swiss_meat_products(
        self,
        page_size: int = 100,
        max_products: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for Swiss meat products in Open Food Facts.

        Args:
            page_size: Number of products per page
            max_products: Maximum number of products to fetch

        Returns:
            List of Swiss meat products with brand information
        """
        products = []
        page = 1

        print(f"Fetching Swiss meat products from Open Food Facts...")

        while True:
            url = (
                f"{self.BASE_URL}/search?"
                f"countries_tags_en=switzerland&"
                f"categories_tags_en=meats&"
                f"page={page}&"
                f"page_size={page_size}&"
                f"fields=code,product_name,brands,brands_tags,categories,categories_tags"
            )

            try:
                data = self._make_request(url)
            except RuntimeError as e:
                print(f"API error: {e}")
                break

            page_products = data.get("products", [])

            if not page_products:
                break

            for product in page_products:
                products.append({
                    "barcode": product.get("code"),
                    "name": product.get("product_name", ""),
                    "brands": product.get("brands", ""),
                    "brands_tags": product.get("brands_tags", []),
                    "categories": product.get("categories", ""),
                    "categories_tags": product.get("categories_tags", []),
                })

            print(f"  Fetched page {page} ({len(products)} products so far)")

            if max_products and len(products) >= max_products:
                products = products[:max_products]
                break

            page += 1

        print(f"Fetched {len(products)} Swiss meat products from Open Food Facts")
        return products

    def save_cache(self, cache_path: Path):
        """Save the in-memory cache to disk.

        Args:
            cache_path: Path to save cache file
        """
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with cache_path.open('w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

        print(f"Saved Open Food Facts cache ({len(self.cache)} entries) to {cache_path}")

    def load_cache(self, cache_path: Path) -> bool:
        """Load cache from disk.

        Args:
            cache_path: Path to cache file

        Returns:
            True if cache was loaded successfully
        """
        if not cache_path.exists():
            return False

        try:
            with cache_path.open('r', encoding='utf-8') as f:
                self.cache = json.load(f)
            print(f"Loaded Open Food Facts cache ({len(self.cache)} entries) from {cache_path}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to load cache {cache_path}: {e}")
            return False
