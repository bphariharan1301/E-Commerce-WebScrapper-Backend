from typing import List, Dict


class CountryMapper:
    def __init__(self):
        self.country_websites = {
            "US": ["amazon", "ebay", "bestbuy", "walmart"],
            "IN": ["amazon", "flipkart"],
            "UK": ["amazon", "ebay"],
            "CA": ["amazon", "ebay"],
            "DE": ["amazon", "ebay"],
            "FR": ["amazon", "ebay"],
            "JP": ["amazon", "ebay"],
            "AU": ["amazon", "ebay"],
            "SG": ["amazon", "ebay"],
            "MY": ["amazon", "ebay"],
            "TH": ["amazon", "ebay"],
            "BR": ["amazon", "ebay"],
            "MX": ["amazon", "ebay"],
        }

    def get_websites_for_country(self, country: str) -> List[str]:
        """Get list of supported websites for a country"""
        return self.country_websites.get(country.upper(), ["amazon", "ebay"])

    def get_supported_countries(self) -> List[str]:
        """Get list of all supported countries"""
        return list(self.country_websites.keys())

    def is_country_supported(self, country: str) -> bool:
        """Check if a country is supported"""
        return country.upper() in self.country_websites
