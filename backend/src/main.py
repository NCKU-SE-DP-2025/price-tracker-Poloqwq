
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi import FastAPI




from src.auth.router import router as auth_router
from src.news.router import router as news_router
from src.news.scheduler import NewsScheduler
from src.price.router import router as price_router


app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/users")
app.include_router(news_router, prefix="/api/v1/news")
app.include_router(price_router, prefix="/api/v1/prices")

news_scheduler = NewsScheduler()

@app.on_event("startup")
def start_scheduler():
    news_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    news_scheduler.shutdown()