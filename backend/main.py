import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )


engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



from urllib.parse import quote
from bs4 import BeautifulSoup
from openai import OpenAI


class OpenAIService:
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_summary(self, content: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
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
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
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
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": title},
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return completion.choices[0].message.content


class NewsScraperService:
    
    BASE_URL = "https://udn.com/api/more"
    
    @staticmethod
    def fetch_news_list(search_term: str, page: int = 1) -> List[dict]:
        params = {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get(NewsScraperService.BASE_URL, params=params)
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


class AuthService:
    
    def __init__(self, db: Session, secret_key: str, algorithm: str = "HS256"):
        self.db = db
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, username: str, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = {"sub": username}
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            return username
        except JWTError:
            return None
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        username = self.decode_token(token)
        if username:
            return self.db.query(User).filter(User.username == username).first()
        return None
    
    def create_user(self, username: str, password: str) -> User:
        hashed_password = self.hash_password(password)
        user = User(username=username, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class PriceService:
    
    BASE_URL = "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice"
    
    @staticmethod
    def get_necessities_prices(category: Optional[str] = None, commodity: Optional[str] = None) -> dict:
        params = {}
        if category:
            params["CategoryName"] = category
        if commodity:
            params["Name"] = commodity
        
        response = requests.get(PriceService.BASE_URL, params=params)
        return response.json()




app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = "xxx"
JWT_SECRET_KEY = "1892dhianiandowqd0n"
TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class UserAuthSchema(BaseModel):
    username: str
    password: str


class PromptRequest(BaseModel):
    prompt: str


class NewsSummaryRequestSchema(BaseModel):
    content: str


# Dependencies
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_openai_service():
    return OpenAIService(api_key=OPENAI_API_KEY)


def get_news_service(
    db: Session = Depends(get_db),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    scraper_service = NewsScraperService()
    return NewsService(db, openai_service, scraper_service)


def get_auth_service(db: Session = Depends(get_db)):
    return AuthService(db, JWT_SECRET_KEY)


def get_upvote_service(db: Session = Depends(get_db)):
    return UpvoteService(db)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, JWT_SECRET_KEY)
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user



@app.post("/api/v1/users/register")
def create_user(
    user_data: UserAuthSchema,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.create_user(user_data.username, user_data.password)
    return {"username": user.username, "id": user.id}


@app.post("/api/v1/users/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth_service.create_access_token(
        username=user.username,
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/users/me")
def read_users_me(user = Depends(get_current_user)):
    return {"username": user.username}


@app.get("/api/v1/news/news")
def read_news(news_service: NewsService = Depends(get_news_service)):
    return news_service.get_all_news(user_id=None)


@app.get("/api/v1/news/user_news")
def read_user_news(
    user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.get_all_news(user_id=user.id)


@app.post("/api/v1/news/search_news")
async def search_news(
    request: PromptRequest,
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.search_news(request.prompt)


@app.post("/api/v1/news/news_summary")
async def news_summary(
    payload: NewsSummaryRequestSchema,
    user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.generate_news_summary(payload.content)


@app.post("/api/v1/news/{article_id}/upvote")
def upvote_article(
    article_id: int,
    user = Depends(get_current_user),
    upvote_service: UpvoteService = Depends(get_upvote_service)
):
    message = upvote_service.toggle_upvote(article_id, user.id)
    return {"message": message}


@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(
    category: str = Query(None),
    commodity: str = Query(None)
):
    return PriceService.get_necessities_prices(category, commodity)




@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    
    if db.query(NewsArticle).count() == 0:
        openai_service = OpenAIService(api_key=OPENAI_API_KEY)
        scraper_service = NewsScraperService()
        news_service = NewsService(db, openai_service, scraper_service)
        news_service.fetch_and_store_news(is_initial=True)
    
    db.close()
    
    def fetch_news_job():
        db = SessionLocal()
        openai_service = OpenAIService(api_key=OPENAI_API_KEY)
        scraper_service = NewsScraperService()
        news_service = NewsService(db, openai_service, scraper_service)
        news_service.fetch_and_store_news(is_initial=False)
        db.close()
    
    background_scheduler.add_job(fetch_news_job, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()