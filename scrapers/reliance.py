# Generic scraper for Reliance Digital (India)
import requests
from bs4 import BeautifulSoup

def fetch_reliance_products(query, country):
    if country.upper() != "IN":
        return []
    url = f"https://www.reliancedigital.in/search?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select(".sp grid cls_sp grid"):
        title = item.select_one(".sp__name")
        price = item.select_one(".sp__offerPrice")
        link = item.select_one("a.sp__product__link")
        if title and price and link:
            results.append({
                "link": f"https://www.reliancedigital.in{link['href']}",
                "price": price.text.replace('₹', '').replace(',', '').strip(),
                "currency": "INR",
                "productName": title.text,
            })
    return results
