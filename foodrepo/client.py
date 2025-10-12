"""FoodRepo API client for fetching product data."""

import os
import time
import requests
from typing import Dict, List, Any, Optional, Iterator
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FoodRepoClient:
    """Client for accessing FoodRepo v3 API."""

    BASE_URL = "https://www.foodrepo.org/api/v3"

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 0.2):
        """Initialize client with API key and rate limiting.

        Args:
            api_key: FoodRepo API key. If None, reads from FOOD_REPO_API_KEY env var
            rate_limit: Seconds to wait between requests (default: 0.2s)
        """
        self.api_key = api_key or os.environ.get("FOOD_REPO_API_KEY")
        if not self.api_key:
            raise ValueError("FoodRepo API key required. Set FOOD_REPO_API_KEY environment variable.")

        self.rate_limit = rate_limit
        self.headers = {
            "authorization": f'Token token="{self.api_key}"',
            "content-type": "application/json",
        }

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make authenticated request to FoodRepo API.

        Args:
            url: Full URL to request

        Returns:
            Parsed JSON response

        Raises:
            requests.RequestException: On API errors
        """
        if self.rate_limit > 0:
            time.sleep(self.rate_limit)

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_products(self, limit: Optional[int] = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """Fetch all products from FoodRepo API with pagination.

        Args:
            limit: Maximum number of products to fetch (None for all)
            page_size: Number of products per API call

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
        url = f"{self.BASE_URL}/products"
        products = []

        print(f"Fetching products from FoodRepo API (limit: {limit or 'all'})...")

        while url:
            print(f"Fetching page... (collected: {len(products)})")

            try:
                data = self._make_request(url)
            except requests.RequestException as e:
                print(f"API request failed: {e}")
                break

            # Extract products from response
            page_products = data.get("data", [])
            for product_data in page_products:
                attrs = product_data.get("attributes", {})

                product = {
                    "barcode": attrs.get("barcode"),
                    "name": attrs.get("name"),
                    "brands": attrs.get("brands"),
                    "categories": attrs.get("categories"),
                    "ingredients_text": attrs.get("ingredients_text"),
                    "origins": attrs.get("origins"),
                    "images": attrs.get("images", []),
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
            except requests.RequestException as e:
                print(f"API request failed: {e}")
                break

            page_products = data.get("data", [])
            for product_data in page_products:
                attrs = product_data.get("attributes", {})

                product = {
                    "barcode": attrs.get("barcode"),
                    "name": attrs.get("name"),
                    "brands": attrs.get("brands"),
                    "categories": attrs.get("categories"),
                    "ingredients_text": attrs.get("ingredients_text"),
                    "origins": attrs.get("origins"),
                    "images": attrs.get("images", []),
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