from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


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
            "JP": "amazon.co.jp",
            "AU": "amazon.com.au",
        }

    def get_search_url(self, query: str, country: str) -> str:
        domain = self.domain_map.get(country, "amazon.com")
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.{domain}/s?k={encoded_query}&ref=sr_pg_1"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        products = []

        try:
            url = self.get_search_url(query, country)
            logger.info(f"Fetching Amazon URL: {url}")
            html = await self.fetch_page(url)

            if not html:
                return products

            soup = BeautifulSoup(html, "html.parser")

            # Amazon product containers
            product_containers = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )

            for container in product_containers[:10]:  # Limit to first 10 results
                try:
                    # Product name
                    name_elem = container.find(
                        "h2", class_="a-size-mini"
                    ) or container.find("span", class_="a-size-medium")
                    product_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Price
                    price_elem = container.find(
                        "span", class_="a-price-whole"
                    ) or container.find("span", class_="a-offscreen")
                    price = self.parse_price(
                        price_elem.get_text(strip=True) if price_elem else "0"
                    )

                    # Link
                    link_elem = (
                        container.find("h2").find("a") if container.find("h2") else None
                    )
                    link = (
                        f"https://www.{self.domain_map.get(country, 'amazon.com')}{link_elem['href']}"
                        if link_elem
                        else ""
                    )

                    # Image
                    img_elem = container.find("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    # Rating
                    rating_elem = container.find("span", class_="a-icon-alt")
                    rating = None
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        try:
                            rating = float(rating_text.split()[0])
                        except:
                            rating = None

                    if product_name and price and float(price) > 0:
                        products.append(
                            {
                                "link": link,
                                "price": price,
                                "currency": (
                                    "USD"
                                    if country == "US"
                                    else "INR" if country == "IN" else "USD"
                                ),
                                "productName": product_name,
                                "website": "Amazon",
                                "availability": "In Stock",
                                "rating": rating,
                                "image_url": image_url,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing Amazon product: {e}")
                    continue

        except Exception as e:
            logger.error(f"Amazon scraping error: {e}")

        return products
