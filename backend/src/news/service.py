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
from src.crawler.udn_crawler import UDNCrawler, NewsWithSummary

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

class NewsService:
    
    def __init__(self, db: Session, openai_service: OpenAIService, scraper_service: UDNCrawler):
        self.db = db
        self.openai_service = openai_service
        self.udn_service = scraper_service
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
            news_list = self.udn_service.startup(search_term)
        else:
            news_list = self.udn_service.get_headline(search_term, page=1)
        
        for news_item in news_list:
            relevance = self.openai_service.assess_relevance(news_item.title)
            
            if relevance == "high":
                detailed_news = self.udn_service.parse(news_item.url)
                
                if detailed_news:
                    summary_data = self.openai_service.generate_summary(detailed_news.content)
                    
                    detailed_news.summary = summary_data["影響"]
                    detailed_news.reason = summary_data["原因"]
                    news_with_summary = NewsWithSummary(
                        title=detailed_news.title,
                        url=detailed_news.url,
                        time=detailed_news.time,
                        content=detailed_news.content,
                        summary=detailed_news.summary,
                        reason=detailed_news.reason
                    )
                    self.udn_service.save(news_with_summary, self.db)
                    
    
    def search_news(self, prompt: str) -> List[dict]:
        keywords = self.openai_service.extract_keywords(prompt)
        
        news_items = self.udn_service.get_headline(keywords, page=1)
        
        news_list = []
        for news_item in news_items:
            detailed_news = self.udn_service.parse(news_item.url)
            
            if detailed_news:
                listed_news = {
                    "title": detailed_news.title,
                    "url": detailed_news.url,
                    "time": detailed_news.time,
                    "content": detailed_news.content,
                }
                listed_news["id"] = next(self._id_counter)
                news_list.append(listed_news)
        
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