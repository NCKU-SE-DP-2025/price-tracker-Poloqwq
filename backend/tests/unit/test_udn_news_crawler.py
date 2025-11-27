import unittest
from unittest.mock import patch, MagicMock
from requests.models import Response
from sqlalchemy.orm import Session
from src.crawler.udn_crawler import UDNCrawler, NewsWithSummary
from src.crawler.exceptions import DomainMismatchException



class TestUDNCrawler(unittest.TestCase):

    def setUp(self):
        self.scraper = UDNCrawler(timeout=5)

    @patch("src.crawler.udn_crawler.requests.get")
    def test_perform_request_success(self, mock_get):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = self.scraper._perform_request(params={"page": 1, "id": "search:technology"})
        self.assertEqual(response, mock_response)
        mock_get.assert_called_once()

    @patch("src.crawler.udn_crawler.requests.get")
    def test_perform_request_failure(self, mock_get):
        mock_get.side_effect = Exception("Network Error")
        with self.assertRaises(Exception):
            self.scraper._perform_request(params={"page": 1, "id": "search:technology"})

    @patch("src.crawler.udn_crawler.requests.get")
    def test_fetch_news_data(self, mock_get):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "lists": [{"title": "Test News", "titleLink": "https://udn.com/news/test-news"}]
        }
        mock_get.return_value = mock_response

        headlines = self.scraper._fetch_news(page=1, search_term="technology")
        self.assertEqual(len(headlines), 1)
        self.assertEqual(headlines[0].title, "Test News")
        self.assertEqual(headlines[0].url, "https://udn.com/news/test-news")

    @patch("src.crawler.udn_crawler.requests.get")
    def test_parse_news(self, mock_get):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = """
            <html>
                <h1 class="article-content__title">Test Title</h1>
                <time class="article-content__time">2023-09-08T00:00:00</time>
                <section class="article-content__editor">
                    <p>Content paragraph 1.</p>
                    <p>Content paragraph 2.</p>
                </section>
            </html>
        """
        mock_get.return_value = mock_response

        news = self.scraper.parse("https://udn.com/news/test-news")
        self.assertEqual(news.title, "Test Title")
        self.assertEqual(news.time, "2023-09-08T00:00:00")
        self.assertEqual(news.content, "Content paragraph 1. Content paragraph 2.")

    def test_create_search_params(self):
        params = self.scraper._create_search_params(page=1, search_term="technology")
        self.assertEqual(params["page"], 1)
        self.assertEqual(params["id"], "search:technology")
        self.assertEqual(params["channelId"], 2)

    @patch("src.crawler.udn_crawler.Session")
    def test_save_news(self, mock_session):
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        news = NewsWithSummary(
            title="Test Title",
            url="https://udn.com/news/test-news",
            time="2023-09-08T00:00:00",
            content="Test Content",
            summary="Test Summary",
            reason="Test Reason",
        )
        self.scraper.save(news, mock_db)

        mock_db.add.assert_called_once()
        self.assertEqual(mock_db.add.call_args[0][0].title, "Test Title")
        mock_db.commit.assert_called_once()

    def test_is_valid_url(self):
        valid_url = "https://udn.com/news/test-news"
        invalid_url = "https://example.com/news/test-news"

        self.assertTrue(self.scraper._is_valid_url(valid_url))
        self.assertFalse(self.scraper._is_valid_url(invalid_url))

    def test_parse_invalid_domain(self):
        invalid_url = "https://example.com/news/test-news"
        with self.assertRaises(DomainMismatchException):
            self.scraper.parse(invalid_url)


if __name__ == "__main__":
    unittest.main()