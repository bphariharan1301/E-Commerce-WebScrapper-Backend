# Generic scraper for Flipkart (India)
import requests
from bs4 import BeautifulSoup

def fetch_flipkart_products(query, country):
    if country.upper() != "IN":
        return []
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select("._1AtVbE"):
        title = item.select_one("._4rR01T")
        price = item.select_one("._30jeq3")
        link = item.select_one("a._1fQZEK")
        if title and price and link:
            results.append({
                "link": f"https://www.flipkart.com{link['href']}",
                "price": price.text.replace('₹', '').replace(',', '').strip(),
                "currency": "INR",
                "productName": title.text,
            })
    return results
