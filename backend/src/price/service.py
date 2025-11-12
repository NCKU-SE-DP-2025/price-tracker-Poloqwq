import requests
from typing import Optional
from .constants import PriceSettings




class PriceService:
    
    def get_necessities_prices(self, category: Optional[str] = None, commodity: Optional[str] = None) -> dict:
        params = {}
        if category:
            params["CategoryName"] = category
        if commodity:
            params["Name"] = commodity

        response = requests.get(PriceSettings.NECESSITIES_PRICE_API_URL, params=params)
        return response.json()