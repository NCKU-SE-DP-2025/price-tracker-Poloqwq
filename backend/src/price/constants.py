from pydantic import BaseModel 


class PriceSettings(BaseModel):
    NECESSITIES_PRICE_API_URL: str = "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice"