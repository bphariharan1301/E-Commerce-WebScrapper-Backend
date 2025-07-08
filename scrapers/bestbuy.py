# Generic scraper for BestBuy (US)
import requests
from bs4 import BeautifulSoup

def fetch_bestbuy_products(query, country):
    if country.upper() != "US":
        return []
    url = f"https://www.bestbuy.com/site/searchpage.jsp?st={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select(".sku-item"):
        title = item.select_one(".sku-header a")
        price = item.select_one(".priceView-customer-price span")
        link = item.select_one(".sku-header a")
        if title and price and link:
            results.append({
                "link": f"https://www.bestbuy.com{link['href']}",
                "price": price.text.replace('$', '').replace(',', '').strip(),
                "currency": "USD",
                "productName": title.text,
            })
    return results
