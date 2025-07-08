import asyncio
import random
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# # Add logs to log.txt file
# logging.basicConfig(
#     filename="log.txt",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )


class AmazonScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.domain_map = {
            "US": "amazon.com",
            "IN": "amazon.in",
            "UK": "amazon.co.uk",
            "CA": "amazon.ca",
            "DE": "amazon.de",
            "FR": "amazon.fr",
            "IT": "amazon.it",
            "ES": "amazon.es",
            "JP": "amazon.co.jp",
            "AU": "amazon.com.au",
            "BR": "amazon.com.br",
            "MX": "amazon.com.mx",
            "NL": "amazon.nl",
            "SG": "amazon.sg",
            "AE": "amazon.ae",
            "SA": "amazon.sa",
            "PL": "amazon.pl",
            "TR": "amazon.com.tr",
            "SE": "amazon.se",
        }

        self.currency_map = {
            "US": "USD",
            "IN": "INR",
            "UK": "GBP",
            "CA": "CAD",
            "DE": "EUR",
            "FR": "EUR",
            "IT": "EUR",
            "ES": "EUR",
            "JP": "JPY",
            "AU": "AUD",
            "BR": "BRL",
            "MX": "MXN",
            "NL": "EUR",
            "SG": "SGD",
            "AE": "AED",
            "SA": "SAR",
            "PL": "PLN",
            "TR": "TRY",
            "SE": "SEK",
        }

        # Amazon-specific selectors for different page layouts
        self.product_selectors = [
            'div[data-component-type="s-search-result"]',
            'div[data-asin]:not([data-asin=""])',
            ".s-result-item",
            ".sg-col-inner .s-widget-container",
        ]

        self.title_selectors = [
            "h2 a span",
            "h2 .a-link-normal span",
            ".s-size-mini span",
            "h2 span",
            ".a-size-base-plus",
            ".a-size-medium",
        ]

        self.price_selectors = [
            ".a-price-whole",
            ".a-price .a-offscreen",
            ".a-price-symbol + .a-price-whole",
            ".a-color-price",
            ".sx-price-whole",
        ]

        self.link_selectors = [
            "h2 a",
            ".a-link-normal",
            'a[href*="/dp/"]',
            'a[href*="/gp/product/"]',
        ]

        self.image_selectors = [
            ".s-image",
            'img[data-image-latency="s-product-image"]',
            ".a-dynamic-image",
        ]

        self.rating_selectors = [
            ".a-icon-alt",
            'span[aria-label*="stars"]',
            ".a-star-medium .a-icon-alt",
        ]

    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers for Amazon requests"""
        headers = super().get_headers()

        # Amazon-specific headers
        amazon_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        headers.update(amazon_headers)
        return headers

    def get_search_url(self, query: str, country: str) -> str:
        """Generate Amazon search URL for specific country"""
        domain = self.domain_map.get(country.upper(), "amazon.com")
        encoded_query = quote_plus(query)

        # Different URL patterns for different Amazon domains
        if domain == "amazon.co.jp":
            return f"https://www.{domain}/s?k={encoded_query}&ref=sr_pg_1"
        else:
            logger.info(
                f"URL for Scrape: {f'https://www.{domain}/s?k={encoded_query}&ref=sr_pg_1'}"
            )
            return f"https://www.{domain}/s?k={encoded_query}&ref=sr_pg_1"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        """Search for products on Amazon"""
        print(f"Searching Amazon for query: {query} in country: {country}")
        products = []
        country_upper = country.upper()

        if country_upper not in self.domain_map:
            logger.warning(f"Country {country} not supported for Amazon")
            return products

        try:
            url = self.get_search_url(query, country)
            logger.info(f"Searching Amazon {country_upper}: {url}")

            # Add random delay to avoid being blocked
            await asyncio.sleep(random.uniform(1, 3))

            html = await self.fetch_page(url)
            if not html:
                logger.warning(f"No HTML content received from Amazon {country_upper}")
                return products

            soup = BeautifulSoup(html, "html.parser")
            logger.info(f"Parsing HTML content for Amazon {soup}")

            # Try different product container selectors
            product_containers = []
            for selector in self.product_selectors:
                containers = soup.select(selector)
                if containers:
                    product_containers = containers
                    logger.info(
                        f"Found {len(containers)} products using selector: {selector}"
                    )
                    break

            if not product_containers:
                logger.warning(f"No product containers found on Amazon {country_upper}")
                return products

            # Parse each product
            for i, container in enumerate(
                product_containers[:15]
            ):  # Limit to 15 results
                try:
                    product = await self._parse_product(container, country_upper)
                    if product and self._is_valid_product(product, query):
                        products.append(product)

                except Exception as e:
                    logger.debug(f"Error parsing product {i+1}: {e}")
                    continue

            logger.info(
                f"Successfully parsed {len(products)} products from Amazon {country_upper}"
            )

        except Exception as e:
            logger.error(f"Amazon {country_upper} scraping error: {e}")

        return products

    async def _parse_product(self, container, country: str) -> Optional[Dict[str, Any]]:
        """Parse individual product from container"""
        try:
            # Extract product name
            product_name = self._extract_product_name(container)
            if not product_name:
                return None

            # Extract price
            price = self._extract_price(container)
            if not price or float(price) <= 0:
                return None

            # Extract link
            link = self._extract_link(container, country)

            # Extract image URL
            image_url = self._extract_image_url(container)

            # Extract rating
            rating = self._extract_rating(container)

            # Extract availability
            availability = self._extract_availability(container)

            # Get currency for country
            currency = self.currency_map.get(country, "USD")

            return {
                "link": link,
                "price": price,
                "currency": currency,
                "productName": product_name,
                "website": "Amazon",
                "availability": availability,
                "rating": rating,
                "image_url": image_url,
            }

        except Exception as e:
            logger.debug(f"Error in _parse_product: {e}")
            return None

    def _extract_product_name(self, container) -> str:
        """Extract product name using multiple selectors"""
        for selector in self.title_selectors:
            elements = container.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Ensure meaningful title
                    # Clean up the title
                    text = re.sub(r"\s+", " ", text)  # Remove extra whitespace
                    text = text.replace("\n", " ").strip()
                    return text[:200]  # Limit length
        return ""

    def _extract_price(self, container) -> str:
        """Extract price using multiple selectors"""
        for selector in self.price_selectors:
            elements = container.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                if price_text:
                    # Clean and extract numeric price
                    price = self._clean_price(price_text)
                    if price and float(price) > 0:
                        return price
        return "0"

    def _extract_link(self, container, country: str) -> str:
        """Extract product link"""
        domain = self.domain_map.get(country, "amazon.com")

        for selector in self.link_selectors:
            elements = container.select(selector)
            for element in elements:
                href = element.get("href", "")
                if href and ("/dp/" in href or "/gp/product/" in href):
                    if href.startswith("http"):
                        return href
                    elif href.startswith("/"):
                        return f"https://www.{domain}{href}"
        return ""

    def _extract_image_url(self, container) -> str:
        """Extract product image URL"""
        for selector in self.image_selectors:
            elements = container.select(selector)
            for element in elements:
                # Try different image URL attributes
                for attr in ["src", "data-src", "data-image-source"]:
                    img_url = element.get(attr, "")
                    if img_url and img_url.startswith("http"):
                        return img_url
        return ""

    def _extract_rating(self, container) -> Optional[float]:
        """Extract product rating"""
        for selector in self.rating_selectors:
            elements = container.select(selector)
            for element in elements:
                rating_text = element.get_text(strip=True)
                if rating_text:
                    # Extract rating from text like "4.5 out of 5 stars"
                    rating_match = re.search(r"(\d+\.?\d*)\s*out of", rating_text)
                    if rating_match:
                        try:
                            return float(rating_match.group(1))
                        except ValueError:
                            continue

                    # Try to extract just the number
                    rating_match = re.search(r"^(\d+\.?\d*)", rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                            if 0 <= rating <= 5:
                                return rating
                        except ValueError:
                            continue
        return None

    def _extract_availability(self, container) -> str:
        """Extract availability information"""
        # Look for availability indicators
        availability_selectors = [
            ".a-color-success",
            ".a-color-price",
            '[data-cy="availability-recipe"]',
            ".a-size-base.a-color-secondary",
        ]

        for selector in availability_selectors:
            elements = container.select(selector)
            for element in elements:
                text = element.get_text(strip=True).lower()
                if any(
                    keyword in text for keyword in ["in stock", "available", "ships"]
                ):
                    return "In Stock"
                elif any(
                    keyword in text for keyword in ["out of stock", "unavailable"]
                ):
                    return "Out of Stock"

        return "In Stock"  # Default assumption

    def _clean_price(self, price_text: str) -> str:
        """Clean and extract numeric price from text"""
        if not price_text:
            return "0"

        # Remove common currency symbols and formatting
        price_text = re.sub(r"[^\d.,]", "", price_text)
        price_text = price_text.replace(",", "")

        # Extract first valid number
        price_match = re.search(r"(\d+\.?\d*)", price_text)
        if price_match:
            try:
                price = float(price_match.group(1))
                return str(price)
            except ValueError:
                pass

        return "0"

    def _is_valid_product(self, product: Dict[str, Any], query: str) -> bool:
        """Validate if product matches search criteria"""
        if not product.get("productName") or not product.get("price"):
            return False

        price = float(product["price"])
        if price <= 0:
            return False

        # Basic relevance check
        product_name_lower = product["productName"].lower()
        query_lower = query.lower()

        # Extract key terms from query
        query_terms = re.findall(r"\b\w+\b", query_lower)
        query_terms = [term for term in query_terms if len(term) > 2]

        if not query_terms:
            return True  # If no meaningful terms, accept the product

        # Check if at least one significant term matches
        matches = sum(1 for term in query_terms if term in product_name_lower)
        return matches > 0

    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """Get detailed information for a specific product"""
        try:
            html = await self.fetch_page(product_url)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            details = {}

            # Extract detailed information
            # Title
            title_element = soup.select_one("#productTitle")
            if title_element:
                details["title"] = title_element.get_text(strip=True)

            # Price
            price_element = soup.select_one(
                ".a-price .a-offscreen, #priceblock_dealprice, #priceblock_ourprice"
            )
            if price_element:
                details["price"] = self._clean_price(price_element.get_text(strip=True))

            # Features
            feature_bullets = soup.select("#feature-bullets ul li")
            if feature_bullets:
                details["features"] = [
                    li.get_text(strip=True) for li in feature_bullets[:5]
                ]

            # Description
            description_element = soup.select_one(
                "#feature-bullets, #productDescription"
            )
            if description_element:
                details["description"] = description_element.get_text(strip=True)[:500]

            return details

        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return {}
