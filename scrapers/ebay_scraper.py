from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EbayScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.domain_map = {
            "US": "ebay.com",
            "IN": "ebay.in",
            "UK": "ebay.co.uk",
            "CA": "ebay.ca",
            "DE": "ebay.de",
            "FR": "ebay.fr",
            "AU": "ebay.com.au",
        }

    def get_search_url(self, query: str, country: str) -> str:
        domain = self.domain_map.get(country, "ebay.com")
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.{domain}/sch/i.html?_nkw={encoded_query}&_sacat=0"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        products = []

        try:
            url = self.get_search_url(query, country)
            html = await self.fetch_page(url)

            if not html:
                return products

            soup = BeautifulSoup(html, "html.parser")

            # eBay product containers
            product_containers = soup.find_all("div", class_="s-item__wrapper")

            for container in product_containers[:10]:
                try:
                    # Product name
                    name_elem = container.find("h3", class_="s-item__title")
                    product_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Price
                    price_elem = container.find("span", class_="s-item__price")
                    price = self.parse_price(
                        price_elem.get_text(strip=True) if price_elem else "0"
                    )

                    # Link
                    link_elem = container.find("a", class_="s-item__link")
                    link = link_elem["href"] if link_elem else ""

                    # Image
                    img_elem = container.find("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

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
                                "website": "eBay",
                                "availability": "In Stock",
                                "rating": None,
                                "image_url": image_url,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing eBay product: {e}")
                    continue

        except Exception as e:
            logger.error(f"eBay scraping error: {e}")

        return products
