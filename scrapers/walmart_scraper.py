from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class WalmartScraper(BaseScraper):
    def get_search_url(self, query: str, country: str) -> str:
        if country != "US":
            return ""  # Walmart is US-specific

        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.walmart.com/search?q={encoded_query}"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        products = []

        if country != "US":
            return products

        try:
            url = self.get_search_url(query, country)
            if not url:
                return products

            html = await self.fetch_page(url)

            if not html:
                return products

            soup = BeautifulSoup(html, "html.parser")

            # Walmart product containers (simplified selectors)
            product_containers = soup.find_all("div", attrs={"data-item-id": True})

            for container in product_containers[:10]:
                try:
                    # Product name
                    name_elem = container.find(
                        "span", attrs={"data-automation-id": "product-title"}
                    )
                    product_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Price
                    price_elem = container.find(
                        "div", class_="price-main"
                    ) or container.find("span", class_="price-current")
                    price = self.parse_price(
                        price_elem.get_text(strip=True) if price_elem else "0"
                    )

                    # Link
                    link_elem = container.find("a")
                    link = (
                        f"https://www.walmart.com{link_elem['href']}"
                        if link_elem and link_elem.get("href")
                        else ""
                    )

                    if product_name and price and float(price) > 0:
                        products.append(
                            {
                                "link": link,
                                "price": price,
                                "currency": "USD",
                                "productName": product_name,
                                "website": "Walmart",
                                "availability": "In Stock",
                                "rating": None,
                                "image_url": "",
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing Walmart product: {e}")
                    continue

        except Exception as e:
            logger.error(f"Walmart scraping error: {e}")

        return products
