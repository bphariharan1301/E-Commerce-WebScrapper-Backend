from abc import ABC, abstractmethod
from typing import List, Dict, Any
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
import random
import time

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self):
        self.session = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def get_session(self):
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=self.get_headers()
            )
        return self.session

    async def fetch_page(self, url: str) -> str:
        """Fetch webpage content with error handling"""
        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""

    async def close(self):
        """Ensure the session is properly closed"""
        if self.session:
            await self.session.close()
            self.session = None

    def parse_price(self, price_text: str) -> str:
        """Extract numeric price from text"""
        if not price_text:
            return "0"

        # Remove common currency symbols and formatting
        price_text = price_text.replace(",", "").replace("$", "").replace("₹", "")

        # Extract first number found
        import re

        match = re.search(r"[\d.]+", price_text)
        return match.group() if match else "0"

    @abstractmethod
    async def search_products(self, query: str, country: str) -> List[Dict[str, Any]]:
        """Search for products on the website"""
        pass

    @abstractmethod
    def get_search_url(self, query: str, country: str) -> str:
        """Generate search URL for the website"""
        pass
