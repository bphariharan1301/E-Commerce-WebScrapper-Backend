# Backend for E-Commerce Price Fetcher

# All backend code and scrapers go here.

# README for backend

## How to run

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

## Docker

```bash
docker build -t price-fetcher-backend .
docker run -p 8000:8000 price-fetcher-backend
```

## Example curl

```
curl -X POST "http://localhost:8000/fetch-prices" -H "Content-Type: application/json" -d '{"country": "US", "query": "iPhone 16 Pro, 128GB"}'
```

## Proof of working

Include a screenshot or video of the above curl command and its output here.
