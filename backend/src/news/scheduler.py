from apscheduler.schedulers.background import BackgroundScheduler
from src.database import SessionLocal
from src.news.service import NewsService, OpenAIService
from src.news.models import NewsArticle
from src.news.config import OPENAI_API_KEY
from src.crawler.udn_crawler import UDNCrawler

class NewsScheduler:
    
    def __init__(self):
        self.background_scheduler = BackgroundScheduler()
        self.udn_crawler = UDNCrawler()
    def start(self):
        db = SessionLocal()
        if db.query(NewsArticle).count() == 0:
            openai_service = OpenAIService(api_key=OPENAI_API_KEY)
            scraper_service = self.udn_crawler
            news_service = NewsService(db, openai_service, scraper_service)
            news_service.fetch_and_store_news(is_initial=True)
    
        db.close()
        
        def fetch_news_job():
            db = SessionLocal()
            openai_service = OpenAIService(api_key=OPENAI_API_KEY)
            scraper_service = self.udn_crawler
            news_service = NewsService(db, openai_service, scraper_service)
            news_service.fetch_and_store_news(is_initial=False)
            db.close()
        
        self.background_scheduler.add_job(fetch_news_job, "interval", minutes=100)
        self.background_scheduler.start()

    def shutdown(self):
        self.background_scheduler.shutdown()