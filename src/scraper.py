"""Core scraping functionality for EMH website."""

import re
import time
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://essenmitherz.ch"
HEADERS = {"User-Agent": "ethicalmeat-scraper/0.1"}

# Regex patterns for extracting ratings
RATING_RE = re.compile(r'\b(TOP|OK|UNCOOL|NO GO)\b', re.I)
STEPS_RE = re.compile(r'(\d+)\s+steps?\s+to\s+go', re.I)

# Known animal types
ANIMALS = ["rindfleisch", "kalbfleisch", "poulet", "schweinefleisch", "eier", "milch"]


class EMHScraper:
    """Main scraper class for Essen mit Herz website."""

    def __init__(self, cache_dir: Optional[Path] = None, rate_limit: float = 1.0):
        """
        Initialize scraper.

        Args:
            cache_dir: Directory to cache HTML responses (None to disable caching)
            rate_limit: Minimum seconds between requests
        """
        self.cache_dir = cache_dir
        self.rate_limit = rate_limit
        self.last_request_time = 0

        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Optional[Path]:
        """Get cache file path for a URL."""
        if not self.cache_dir:
            return None
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.html"

    def _get_html(self, url: str) -> str:
        """
        Fetch HTML from URL with caching and rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        # Check cache first
        cache_path = self._get_cache_path(url)
        if cache_path and cache_path.exists():
            return cache_path.read_text(encoding='utf-8')

        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        # Fetch
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        html = response.text
        self.last_request_time = time.time()

        # Cache
        if cache_path:
            cache_path.write_text(html, encoding='utf-8')

        return html

    def discover_label_urls(self) -> List[str]:
        """
        Discover all label URLs from the main label index page.

        Returns:
            List of label URLs
        """
        url = f"{BASE_URL}/label-und-marken/"
        html = self._get_html(url)
        soup = BeautifulSoup(html, "lxml")

        urls = set()
        for a in soup.select("a[href*='/label-']"):
            href = a.get("href", "")
            if href:
                urls.add(urljoin(BASE_URL, href))

        return sorted(urls)

    def parse_label_page(self, url: str) -> Dict[str, Any]:
        """
        Parse a label page to extract animal product links.

        Args:
            url: Label page URL

        Returns:
            Dictionary with label info and product links
        """
        html = self._get_html(url)
        soup = BeautifulSoup(html, "lxml")

        # Extract title from <title> tag (no h1 exists on label pages)
        title_elem = soup.select_one("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove the site suffix " – Essen mit Herz"
            title = title_text.split(" – ")[0] if " – " in title_text else title_text
            # Remove "Label " prefix if present
            if title.startswith("Label "):
                title = title[6:]
        else:
            title = None

        # Find "Produkte:" section - products are in a post-grid div
        products = []

        # Look for the post-grid div that contains the products
        post_grid = soup.find("div", {"id": re.compile(r"post-grid-\d+")})

        if post_grid:
            # Find all links within the grid items
            for a in post_grid.find_all("a", href=True):
                href = a.get("href", "")

                # Filter for actual product links (not images, must have animal keywords in URL)
                if any(animal in href for animal in ANIMALS):
                    text = a.get_text(" ", strip=True)

                    # Skip if it's just an empty link (image link)
                    if not text or len(text) < 5:
                        continue

                    full_url = urljoin(BASE_URL, href)

                    # Detect animal type from link text or URL
                    animal = None
                    for animal_type in ANIMALS:
                        if text.lower().startswith(animal_type) or f"/{animal_type}-" in href:
                            animal = animal_type
                            break

                    products.append({
                        "animal_text": text,
                        "animal": animal,
                        "url": full_url
                    })

        return {
            "label_url": url,
            "label_title": title,
            "products": products
        }

    def parse_product_page(self, url: str) -> Dict[str, Any]:
        """
        Parse an animal product page to extract rating information.

        Args:
            url: Product page URL

        Returns:
            Dictionary with product info and rating
        """
        html = self._get_html(url)
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else None

        # Get page text for regex extraction
        content = soup.select_one("article") or soup
        text = content.get_text("\n", strip=True)

        # Extract tier (TOP/OK/UNCOOL/NO GO)
        tier = None
        m_tier = RATING_RE.search(text)
        if m_tier:
            tier = m_tier.group(1).upper()

        # Extract steps to go
        steps = None
        m_steps = STEPS_RE.search(text)
        if m_steps:
            steps = int(m_steps.group(1))

        # Detect animal from title or URL
        animal = None
        if title:
            for animal_type in ANIMALS:
                if title.lower().startswith(animal_type):
                    animal = animal_type
                    break

        if not animal:
            for animal_type in ANIMALS:
                if f"/{animal_type}-" in url or f"/{animal_type}/" in url:
                    animal = animal_type
                    break

        return {
            "url": url,
            "title": title,
            "animal": animal,
            "tier": tier,
            "steps_to_go": steps
        }

    def harvest_all_ratings(self) -> List[Dict[str, Any]]:
        """
        Harvest all label-animal-rating combinations from the EMH website.

        Returns:
            List of dictionaries with label, animal, and rating info
        """
        results = []

        # Discover all labels
        label_urls = self.discover_label_urls()
        print(f"Found {len(label_urls)} labels")

        # Process each label
        for i, label_url in enumerate(label_urls, 1):
            print(f"[{i}/{len(label_urls)}] Processing: {label_url}")

            try:
                label_data = self.parse_label_page(label_url)
                label_name = label_data["label_title"]

                # Process each animal product for this label
                for product in label_data["products"]:
                    try:
                        product_data = self.parse_product_page(product["url"])

                        results.append({
                            "label": label_name,
                            "label_url": label_url,
                            "animal": product["animal"] or product_data["animal"],
                            "product_title": product_data["title"],
                            "product_url": product_data["url"],
                            "tier": product_data["tier"],
                            "steps_to_go": product_data["steps_to_go"]
                        })

                        print(f"  ✓ {product_data['title']}: {product_data['tier']}")
                    except Exception as e:
                        print(f"  ✗ Error parsing {product['url']}: {e}")

            except Exception as e:
                print(f"  ✗ Error parsing label page: {e}")

        return results
