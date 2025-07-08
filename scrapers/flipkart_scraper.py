from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    def get_search_url(self, query: str, country: str) -> str:
        if country != "IN":
            return ""  # Flipkart is India-specific

        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.flipkart.com/search?q={encoded_query}"

    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        products = []

        if country != "IN":
            return products

        try:
            url = self.get_search_url(query, country)
            if not url:
                return products

            html = await self.fetch_page(url)

            if not html:
                return products

            soup = BeautifulSoup(html, "html.parser")

            # Flipkart product containers
            product_containers = soup.find_all(
                "div", class_="_1AtVbE"
            ) or soup.find_all("div", class_="_4rR01T")

            for container in product_containers[:10]:
                try:
                    # Product name
                    name_elem = container.find(
                        "div", class_="_4rR01T"
                    ) or container.find("a", class_="IRpwTa")
                    product_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Price
                    price_elem = container.find(
                        "div", class_="_30jeq3"
                    ) or container.find("div", class_="_30jeq3 _1_WHN1")
                    price = self.parse_price(
                        price_elem.get_text(strip=True) if price_elem else "0"
                    )

                    # Link
                    link_elem = container.find("a")
                    link = (
                        f"https://www.flipkart.com{link_elem['href']}"
                        if link_elem and link_elem.get("href")
                        else ""
                    )

                    # Image
                    img_elem = container.find("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    # Rating
                    rating_elem = container.find("div", class_="_3LWZlK")
                    rating = None
                    if rating_elem:
                        try:
                            rating = float(rating_elem.get_text(strip=True))
                        except:
                            rating = None

                    if product_name and price and float(price) > 0:
                        products.append(
                            {
                                "link": link,
                                "price": price,
                                "currency": "INR",
                                "productName": product_name,
                                "website": "Flipkart",
                                "availability": "In Stock",
                                "rating": rating,
                                "image_url": image_url,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing Flipkart product: {e}")
                    continue

        except Exception as e:
            logger.error(f"Flipkart scraping error: {e}")

        return products
