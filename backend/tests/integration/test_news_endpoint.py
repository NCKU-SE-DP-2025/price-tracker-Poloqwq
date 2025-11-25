import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import json
from jose import jwt
from src.main import app

from src.database import Base, get_db as session_opener
from src.news.models import NewsArticle
from src.auth.models import User

from src.news.schemas import NewsSummaryRequestSchema
from src.auth.config import PWD_CONTEXT as pwd_context
from unittest.mock import Mock


SECRET_KEY = "1892dhianiandowqd0n"
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_session_opener():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[session_opener] = override_session_opener
client = TestClient(app)

@pytest.fixture(scope="module")
def clear_users():
    with next(override_session_opener()) as db:
        db.query(User).delete()
        db.commit()

@pytest.fixture(scope="module")
def test_user(clear_users):
    hashed_password = pwd_context.hash("testpassword")

    with next(override_session_opener()) as db:
        user = User(username="testuser", hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_token(test_user):
    access_token = jwt.encode({"sub": test_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


@pytest.fixture(scope="function")
def test_articles():
    with next(override_session_opener()) as db:
        db.query(NewsArticle).delete()
        db.commit()

        article_1 = NewsArticle(
            url="https://example.com/test-news-1",
            title="Test News 1",
            content="This is test content 1",
            time="2024-01-01",
            summary="Test summary 1",
            reason="Test reason 1"
        )
        article_2 = NewsArticle(
            url="https://example.com/test-news-2",
            title="Test News 2",
            content="This is test content 2",
            time="2024-01-02",
            summary="Test summary 2",
            reason="Test reason 2"
        )

        db.add_all([article_1, article_2])
        db.commit()
        db.refresh(article_1)
        db.refresh(article_2)

        return [article_1, article_2]


@pytest.fixture(scope="function")
def test_user_and_articles(test_user, test_articles):
    return test_user, test_articles


def test_read_news(test_articles):
    response = client.get("/api/v1/news/news")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[1]["title"] == "Test News 1"


def test_read_user_news(test_user, test_token, test_articles):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/news/user_news", headers=headers)
    print(test_token)
    print(response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[0]["is_upvoted"] is False
    assert json_response[1]["title"] == "Test News 1"
    assert json_response[1]["is_upvoted"] is False

def mock_openai(mocker, return_content):
    mock_openai_client = mocker.patch('src.news.service.OpenAI')

    mock_message = Mock()
    mock_message.content = return_content

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_openai_client.return_value.chat.completions.create.return_value = mock_completion

    return mock_openai_client

def test_search_news(mocker):
    mock_openai(mocker, "keywords")

    mocker.patch("src.news.service.NewsScraperService.fetch_news_list_multiple_pages", return_value=[
        {"titleLink": "http://example.com/news1"}
    ])

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"lists": [
        {"titleLink": "http://example.com/news1"}
    ]}
    mock_response.text = """
        <html>
        <h1 class="article-content__title">Test Title</h1>
        <time class="article-content__time">2024-09-10</time>
        <section class="article-content__editor">
            <p>This is a test paragraph.</p>
        </section>
        </html>
    """

    mocker.patch("requests.get", return_value=mock_response)

    request_body = {"prompt": "Test search prompt"}

    response = client.post("/api/v1/news/search_news", json=request_body)

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Title"
    assert data[0]["time"] == "2024-09-10"
    assert data[0]["content"] == "This is a test paragraph."


def test_news_summary(mocker, test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    openai_response = json.dumps({"影響": "test impact", "原因": "test reason"})
    mock_openai(mocker, openai_response)

    request_body = NewsSummaryRequestSchema(content="Test news content")
    response = client.post("/api/v1/news/news_summary", json=request_body.dict(), headers=headers)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["summary"] == "test impact"
    assert json_response["reason"] == "test reason"


def test_upvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Article upvoted"


def test_downvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Upvote removed"
