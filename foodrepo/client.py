"""FoodRepo API client for fetching product data."""

import os
import time
import subprocess
from typing import Dict, List, Any, Optional, Iterator
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FoodRepoClient:
    """Client for accessing FoodRepo v3 API."""

    BASE_URL = "https://www.foodrepo.org/api/v3"

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 0.2, page_size: int = 1000):
        """Initialize client with API key and rate limiting.

        Args:
            api_key: FoodRepo API key. If None, reads from FOOD_REPO_API_KEY env var
            rate_limit: Seconds to wait between requests (default: 0.2s)
            page_size: Number of products per page (default: 1000, max depends on API)
        """
        self.api_key = api_key or os.environ.get("FOOD_REPO_API_KEY")
        if not self.api_key:
            raise ValueError("FoodRepo API key required. Set FOOD_REPO_API_KEY environment variable.")

        self.rate_limit = rate_limit
        self.page_size = page_size

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make authenticated request to FoodRepo API using curl with --http1.1.

        Args:
            url: Full URL to request

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: On API errors
        """
        if self.rate_limit > 0:
            time.sleep(self.rate_limit)

        # Use curl with --http1.1 to bypass Cloudflare blocking
        curl_command = [
            "curl",
            "-sS",  # silent but show errors
            "-g",   # disable URL globbing (needed for brackets in query params)
            url,
            "-H", "Accept: application/json",
            "-H", "User-Agent: ethicalmeat-db/0.1 (+you@example.com)",
            "-H", f"Authorization: Token token={self.api_key}",
            "--http1.1"
        ]

        result = subprocess.run(curl_command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FoodRepo API request failed: {result.stderr}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse FoodRepo API response: {e}\nResponse: {result.stdout[:500]}")

    def fetch_products(self, limit: Optional[int] = None, page_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all products from FoodRepo API with pagination.

        Args:
            limit: Maximum number of products to fetch (None for all)
            page_size: Number of products per API call (uses instance default if None)

        Returns:
            List of product dictionaries with keys:
            - barcode: Product GTIN/barcode
            - name: Product name
            - brands: Brand information
            - categories: Product categories
            - ingredients_text: Ingredient list
            - origins: Product origins
            - images: List of image URLs
        """
        if page_size is None:
            page_size = self.page_size

        # Build initial URL with page size and exclude heavy fields
        url = f"{self.BASE_URL}/products?page[size]={page_size}&excludes=images,nutrients"
        products = []

        print(f"Fetching products from FoodRepo API (limit: {limit or 'all'}, page_size: {page_size})...")

        while url:
            print(f"Fetching page... (collected: {len(products)})")

            try:
                data = self._make_request(url)
            except RuntimeError as e:
                print(f"API request failed: {e}")
                break

            # Extract products from response
            page_products = data.get("data", [])
            for product_data in page_products:
                # API v3 returns data directly, not wrapped in "attributes"
                # Get name from name_translations or display_name_translations
                name_trans = product_data.get("name_translations") or product_data.get("display_name_translations", {})
                name = name_trans.get("de") or name_trans.get("en") or name_trans.get("fr") or name_trans.get("it") or ""

                # Get ingredients from ingredients_translations
                ingredients_trans = product_data.get("ingredients_translations", {})
                ingredients = ingredients_trans.get("de") or ingredients_trans.get("en") or ingredients_trans.get("fr") or ingredients_trans.get("it") or ""

                # Note: FoodRepo v3 API does not provide brands or categories fields
                product = {
                    "barcode": product_data.get("barcode"),
                    "name": name,
                    "ingredients_text": ingredients,
                    "origins": product_data.get("origins", []),
                }

                # Only add products with barcodes
                if product["barcode"]:
                    products.append(product)

            # Check if we've reached the limit
            if limit and len(products) >= limit:
                products = products[:limit]
                break

            # Get next page URL
            links = data.get("links", {})
            url = links.get("next")

            # No more pages
            if not url:
                break

        print(f"Collected {len(products)} products from FoodRepo")
        return products

    def fetch_products_streaming(self, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Stream products one by one to reduce memory usage.

        Args:
            limit: Maximum number of products to yield

        Yields:
            Product dictionaries
        """
        url = f"{self.BASE_URL}/products"
        count = 0

        while url:
            try:
                data = self._make_request(url)
            except RuntimeError as e:
                print(f"API request failed: {e}")
                break

            page_products = data.get("data", [])
            for product_data in page_products:
                # API v3 returns data directly, not wrapped in "attributes"
                # Get name from name_translations or display_name_translations
                name_trans = product_data.get("name_translations") or product_data.get("display_name_translations", {})
                name = name_trans.get("de") or name_trans.get("en") or name_trans.get("fr") or name_trans.get("it") or ""

                # Get ingredients from ingredients_translations
                ingredients_trans = product_data.get("ingredients_translations", {})
                ingredients = ingredients_trans.get("de") or ingredients_trans.get("en") or ingredients_trans.get("fr") or ingredients_trans.get("it") or ""

                # Note: FoodRepo v3 API does not provide brands or categories fields
                product = {
                    "barcode": product_data.get("barcode"),
                    "name": name,
                    "ingredients_text": ingredients,
                    "origins": product_data.get("origins", []),
                }

                # Only yield products with barcodes
                if product["barcode"]:
                    yield product
                    count += 1

                    if limit and count >= limit:
                        return

            # Get next page URL
            links = data.get("links", {})
            url = links.get("next")

            if not url:
                break

    def save_products_cache(self, products: List[Dict[str, Any]], cache_path: Path) -> None:
        """Save products to cache file.

        Args:
            products: List of product dictionaries
            cache_path: Path to save cache file
        """
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with cache_path.open('w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(products)} products to cache: {cache_path}")

    def load_products_cache(self, cache_path: Path) -> Optional[List[Dict[str, Any]]]:
        """Load products from cache file.

        Args:
            cache_path: Path to cache file

        Returns:
            List of products or None if cache doesn't exist
        """
        if not cache_path.exists():
            return None

        try:
            with cache_path.open('r', encoding='utf-8') as f:
                products = json.load(f)
            print(f"Loaded {len(products)} products from cache: {cache_path}")
            return products
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to load cache {cache_path}: {e}")
            return None