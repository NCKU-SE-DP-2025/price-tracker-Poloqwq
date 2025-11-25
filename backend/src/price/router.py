from fastapi import APIRouter, Query
from src.price.service import PriceService

router = APIRouter()

@router.get("/necessities-price")
def get_necessities_prices(category: str = Query(None), commodity: str = Query(None)):
    return PriceService.get_necessities_prices(category, commodity)