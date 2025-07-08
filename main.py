from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import logging
from scrapers.scraper_manager import ScraperManager
from utils.ai_validator import AIValidator
from utils.country_mapper import CountryMapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Price Scraper", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    country: str
    query: str


class ProductResult(BaseModel):
    link: str
    price: str
    currency: str
    productName: str
    website: str
    availability: str = "In Stock"
    rating: float = None
    image_url: str = None


@app.post("/search", response_model=List[ProductResult])
async def search_products(request: SearchRequest):
    """
    Search for products across multiple e-commerce websites
    """
    try:
        logger.info(f"Searching for '{request.query}' in country '{request.country}'")

        # Initialize components
        scraper_manager = ScraperManager()
        ai_validator = AIValidator()
        country_mapper = CountryMapper()

        # Get relevant websites for the country
        websites = country_mapper.get_websites_for_country(request.country)

        if not websites:
            raise HTTPException(
                status_code=400,
                detail=f"No supported websites found for country: {request.country}",
            )

        # Scrape all websites concurrently
        tasks = []
        logger.info(f"Scraping websites: {websites}")
        for website in websites:
            task = scraper_manager.scrape_website(
                website, request.query, request.country
            )
            tasks.append(task)

        # Wait for all scraping tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter results
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")

        # Validate and rank results using AI
        validated_products = await ai_validator.validate_and_rank(
            all_products, request.query
        )

        # # Sort by price (ascending)
        # validated_products.sort(
        #     key=lambda x: float(
        #         x.price.replace("$", "").replace(",", "").replace("₹", "")
        #     )
        # )

        logger.info(f"Found {len(validated_products)} products")
        return all_products

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/supported-countries")
async def get_supported_countries():
    """Get list of supported countries"""
    country_mapper = CountryMapper()
    return {"countries": country_mapper.get_supported_countries()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
