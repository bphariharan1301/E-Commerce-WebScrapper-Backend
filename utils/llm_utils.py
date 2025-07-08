from ..scrapers.amazon import fetch_amazon_products
from ..scrapers.flipkart import fetch_flipkart_products
from ..scrapers.bestbuy import fetch_bestbuy_products
from ..scrapers.reliance import fetch_reliance_products

def get_sites_for_country(country):
    mapping = {
        "US": ["amazon", "bestbuy"],
        "IN": ["amazon", "flipkart", "reliance"],
    }
    return mapping.get(country.upper(), ["amazon"])

def llm_extract_products(query, country, site):
    # Placeholder for LLM/AI-based extraction for new sites
    return []
