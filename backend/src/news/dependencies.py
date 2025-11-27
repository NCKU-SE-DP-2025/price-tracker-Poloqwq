from fastapi import Depends
from sqlalchemy.orm import Session
from src.news.service import NewsService, OpenAIService, UpvoteService
from src.crawler.udn_crawler import UDNCrawler
from src.database import get_db
from src.news.config import OPENAI_API_KEY


def get_openai_service():
    return OpenAIService(api_key=OPENAI_API_KEY)

def get_news_service(
    db: Session = Depends(get_db),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    scraper_service = UDNCrawler()
    return NewsService(db, openai_service, scraper_service)


def get_upvote_service(db: Session = Depends(get_db)):
    return UpvoteService(db)

