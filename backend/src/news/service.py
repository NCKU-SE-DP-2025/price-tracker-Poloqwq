from typing import List, Optional
import requests
import json
import itertools
from urllib.parse import quote
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from openai import OpenAI
from src.news.models import NewsArticle, user_news_association_table
from src.news.config import NewsConfig

class OpenAIService:
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_summary(self, content: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": NewsConfig.AI_SUMMARY_PROMPT,
            },
            {"role": "user", "content": content},
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        result = completion.choices[0].message.content
        return json.loads(result)
    
    def extract_keywords(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": NewsConfig.AI_KEYWORD_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return completion.choices[0].message.content
    
    def assess_relevance(self, title: str) -> str:
        messages = [
            {
                "role": "system",
                "content": NewsConfig.AI_RELEVANCE_PROMPT,
            },
            {"role": "user", "content": title},
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return completion.choices[0].message.content


class NewsScraperService:
    
    
    @staticmethod
    def fetch_news_list(search_term: str, page: int = 1) -> List[dict]:
        params = {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get(NewsConfig.UDN_API_URL, params=params)
        return response.json()["lists"]
    
    @staticmethod
    def fetch_news_list_multiple_pages(search_term: str, num_pages: int = 9) -> List[dict]:
        all_news = []
        for page in range(1, num_pages + 1):
            news_list = NewsScraperService.fetch_news_list(search_term, page)
            all_news.extend(news_list)
        return all_news
    
    @staticmethod
    def scrape_article_details(url: str) -> Optional[dict]:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            
            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            
            return {
                "url": url,
                "title": title,
                "time": time,
                "content": paragraphs,
            }
        except Exception as e:
            print(f"Error scraping article {url}: {e}")
            return None


class NewsService:
    
    def __init__(self, db: Session, openai_service: OpenAIService, scraper_service: NewsScraperService):
        self.db = db
        self.openai_service = openai_service
        self.scraper_service = scraper_service
        self._id_counter = itertools.count(start=1000000)
    
    def add_article_to_db(self, news_data: dict) -> None:
        article = NewsArticle(
            url=news_data["url"],
            title=news_data["title"],
            time=news_data["time"],
            content=" ".join(news_data["content"]) if isinstance(news_data["content"], list) else news_data["content"],
            summary=news_data["summary"],
            reason=news_data["reason"],
        )
        self.db.add(article)
        self.db.commit()
    
    def fetch_and_store_news(self, search_term: str = "價格", is_initial: bool = False) -> None:
        if is_initial:
            news_list = self.scraper_service.fetch_news_list_multiple_pages(search_term)
        else:
            news_list = self.scraper_service.fetch_news_list(search_term)
        
        for news_item in news_list:
            relevance = self.openai_service.assess_relevance(news_item["title"])
            
            if relevance == "high":
                detailed_news = self.scraper_service.scrape_article_details(news_item["titleLink"])
                
                if detailed_news:
                    content_text = " ".join(detailed_news["content"])
                    summary_data = self.openai_service.generate_summary(content_text)
                    
                    detailed_news["summary"] = summary_data["影響"]
                    detailed_news["reason"] = summary_data["原因"]
                    
                    self.add_article_to_db(detailed_news)
    
    def search_news(self, prompt: str) -> List[dict]:
        keywords = self.openai_service.extract_keywords(prompt)
        
        news_items = self.scraper_service.fetch_news_list(keywords)
        
        news_list = []
        for news_item in news_items:
            detailed_news = self.scraper_service.scrape_article_details(news_item["titleLink"])
            
            if detailed_news:
                detailed_news["content"] = " ".join(detailed_news["content"])
                detailed_news["id"] = next(self._id_counter)
                news_list.append(detailed_news)
        
        return sorted(news_list, key=lambda x: x["time"], reverse=True)
    
    def generate_news_summary(self, content: str) -> dict:
        summary_data = self.openai_service.generate_summary(content)
        return {
            "summary": summary_data["影響"],
            "reason": summary_data["原因"]
        }
    
    def get_all_news(self, user_id: Optional[int] = None) -> List[dict]:
        news_articles = self.db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        
        result = []
        for article in news_articles:
            upvotes, is_upvoted = self._get_article_upvote_details(article.id, user_id)
            result.append({
                **article.__dict__,
                "upvotes": upvotes,
                "is_upvoted": is_upvoted,
            })
        
        return result
    
    def _get_article_upvote_details(self, article_id: int, user_id: Optional[int]) -> tuple:
        upvote_count = (
            self.db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )
        
        is_upvoted = False
        if user_id:
            is_upvoted = (
                self.db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first()
                is not None
            )
        
        return upvote_count, is_upvoted


class UpvoteService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def toggle_upvote(self, article_id: int, user_id: int) -> str:
        existing_upvote = self.db.execute(
            select(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
        ).scalar()
        
        if existing_upvote:
            delete_stmt = delete(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
            self.db.execute(delete_stmt)
            self.db.commit()
            return "Upvote removed"
        else:
            insert_stmt = insert(user_news_association_table).values(
                news_articles_id=article_id, user_id=user_id
            )
            self.db.execute(insert_stmt)
            self.db.commit()
            return "Article upvoted"