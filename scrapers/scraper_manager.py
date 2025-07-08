import asyncio
from typing import List, Dict, Any
import logging
from .amazon import AmazonScraper
from .flipkart_scraper import FlipkartScraper
from .ebay_scraper import EbayScraper
from .bestbuy_scraper import BestBuyScraper
from .walmart_scraper import WalmartScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    def __init__(self):
        self.scrapers = {
            "amazon": AmazonScraper(),
            "flipkart": FlipkartScraper(),
            "ebay": EbayScraper(),
            "bestbuy": BestBuyScraper(),
            "walmart": WalmartScraper(),
        }

    async def scrape_website(
        self, website: str, query: str, country: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape a specific website for products
        """
        try:
            if website not in self.scrapers:
                logger.warning(f"No scraper available for website: {website}")
                return []

            scraper = self.scrapers[website]
            logger.info(f"Scrapper Object: {scraper}")
            results = await scraper.search_products(query, country)
            logger.info(f"Results from {website}: {results}")
            logger.info(f"Scraped {len(results)} products from {website}")
            return results

        except Exception as e:
            logger.error(f"Error scraping {website}: {e}")
            return []
        finally:
            # Ensure the scraper session is closed
            scraper = self.scrapers.get(website)
            if scraper:
                await scraper.close()

    async def scrape_all_websites(
        self, websites: List[str], query: str, country: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple websites concurrently
        """
        tasks = []
        for website in websites:
            task = self.scrape_website(website, query, country)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)

        return all_products
