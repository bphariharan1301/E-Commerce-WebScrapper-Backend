from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BestBuyScraper(BaseScraper):
    def get_search_url(self, query: str, country: str) -> str:
        if country != "US":
            return ""  # Best Buy is US-specific

        # Properly encode the query to avoid issues with special characters
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_query}"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        products = []

        if country != "US":
            return products

        try:
            url = self.get_search_url(query, country)
            if not url:
                return products

            logger.info(f"Fetching Best Buy URL: {url}")
            html = await self.fetch_page(url)

            if not html:
                logger.warning(f"Failed to fetch Best Buy page for query: {query}")
                return products

            soup = BeautifulSoup(html, "html.parser")

            # Best Buy product containers
            product_containers = soup.find_all("li", class_="sku-item")

            if not product_containers:
                logger.warning(
                    f"No product containers found on Best Buy for query: {query}"
                )
                return products

            for container in product_containers[:10]:  # Limit to first 10 results
                try:
                    # Product name
                    name_elem = container.find("h4", class_="sku-header")
                    product_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Price
                    price_elem = container.find(
                        "span", class_="sr-only"
                    ) or container.find("span", attrs={"aria-label": True})
                    price = self.parse_price(
                        price_elem.get_text(strip=True) if price_elem else "0"
                    )

                    # Link
                    link_elem = (
                        container.find("h4").find("a") if container.find("h4") else None
                    )
                    link = (
                        f"https://www.bestbuy.com{link_elem['href']}"
                        if link_elem
                        else ""
                    )

                    # Image
                    img_elem = container.find("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    if product_name and price and float(price) > 0:
                        products.append(
                            {
                                "link": link,
                                "price": price,
                                "currency": "USD",
                                "productName": product_name,
                                "website": "Best Buy",
                                "availability": "In Stock",
                                "rating": None,
                                "image_url": image_url,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing Best Buy product: {e}")
                    continue

        except Exception as e:
            logger.error(f"Best Buy scraping error: {e}")

        return products
