from typing import List, Dict, Any
import logging
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class AIValidator:
    def __init__(self):
        self.relevance_threshold = 0.3

    async def validate_and_rank(
        self, products: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        Validate products against query and rank them by relevance
        """
        validated_products = []

        for product in products:
            relevance_score = self.calculate_relevance(product["productName"], query)

            if relevance_score >= self.relevance_threshold:
                product["relevance_score"] = relevance_score
                validated_products.append(product)

        # Sort by relevance score (descending) then by price (ascending)
        validated_products.sort(
            key=lambda x: (-x["relevance_score"], float(x["price"]))
        )

        # Remove relevance_score from final output
        for product in validated_products:
            product.pop("relevance_score", None)

        return validated_products

    def calculate_relevance(self, product_name: str, query: str) -> float:
        """
        Calculate relevance score between product name and search query
        """
        if not product_name or not query:
            return 0.0

        # Normalize strings
        product_name = product_name.lower().strip()
        query = query.lower().strip()

        # Extract key terms from query
        query_terms = self.extract_key_terms(query)
        product_terms = self.extract_key_terms(product_name)

        # Calculate different similarity metrics
        exact_match_score = self.exact_match_score(product_terms, query_terms)
        sequence_similarity = SequenceMatcher(None, product_name, query).ratio()
        brand_model_score = self.brand_model_match_score(product_name, query)

        # Weighted combination of scores
        final_score = (
            exact_match_score * 0.5
            + sequence_similarity * 0.3
            + brand_model_score * 0.2
        )

        return min(final_score, 1.0)

    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }

        # Split by common delimiters
        terms = re.findall(r"\b\w+\b", text.lower())

        # Filter out stop words and short terms
        meaningful_terms = [
            term for term in terms if term not in stop_words and len(term) > 2
        ]

        return meaningful_terms

    def exact_match_score(
        self, product_terms: List[str], query_terms: List[str]
    ) -> float:
        """Calculate score based on exact term matches"""
        if not query_terms:
            return 0.0

        matches = sum(1 for term in query_terms if term in product_terms)
        return matches / len(query_terms)

    def brand_model_match_score(self, product_name: str, query: str) -> float:
        """Calculate score based on brand and model matching"""
        # Common brands and their variations
        brands = {
            "apple": ["apple", "iphone"],
            "samsung": ["samsung", "galaxy"],
            "boat": ["boat", "boAt"],
            "sony": ["sony"],
            "lg": ["lg"],
            "dell": ["dell"],
            "hp": ["hp", "hewlett"],
            "nike": ["nike"],
            "adidas": ["adidas"],
        }

        score = 0.0
        for brand, variations in brands.items():
            if any(var in query.lower() for var in variations):
                if any(var in product_name.lower() for var in variations):
                    score += 0.5

        # Check for model numbers/specific identifiers
        query_numbers = re.findall(r"\d+", query)
        product_numbers = re.findall(r"\d+", product_name)

        if query_numbers and product_numbers:
            number_matches = sum(1 for num in query_numbers if num in product_numbers)
            score += (number_matches / len(query_numbers)) * 0.5

        return min(score, 1.0)
