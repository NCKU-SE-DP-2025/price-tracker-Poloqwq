from fastapi import APIRouter, Depends
from src.news.dependencies import get_news_service, get_upvote_service
from src.auth.dependencies import get_current_user
from src.news.service import NewsService, UpvoteService
from src.news.schemas import PromptRequest, NewsSummaryRequestSchema
router = APIRouter()





@router.get("/news")
def read_news(news_service: NewsService = Depends(get_news_service)):
    return news_service.get_all_news(user_id=None)


@router.get("/user_news")
def read_user_news(
    user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.get_all_news(user_id=user.id)


@router.post("/search_news")
async def search_news(
    request: PromptRequest,
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.search_news(request.prompt)


@router.post("/news_summary")
async def news_summary(
    payload: NewsSummaryRequestSchema,
    user = Depends(get_current_user),
    news_service: NewsService = Depends(get_news_service)
):
    return news_service.generate_news_summary(payload.content)


@router.post("/{article_id}/upvote")
def upvote_article(
    article_id: int,
    user = Depends(get_current_user),
    upvote_service: UpvoteService = Depends(get_upvote_service)
):
    message = upvote_service.toggle_upvote(article_id, user.id)
    return {"message": message}