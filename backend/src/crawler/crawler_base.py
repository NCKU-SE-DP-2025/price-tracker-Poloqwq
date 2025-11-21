import abc
from pydantic import AnyHttpUrl
from tldextract import tldextract
from sqlalchemy.orm import Session

from src.crawler.exceptions import DomainMismatchException

from pydantic import BaseModel, Field, AnyHttpUrl


class Headline(BaseModel):
    title: str = Field(
        default=...,
        example="Title of the article",
        description="The title of the article"
    )
    url: AnyHttpUrl | str = Field(
        default=...,
        example="https://www.example.com",
        description="The URL of the article"
    )


class News(Headline):
    time: str = Field(
        default=...,
        example="2021-10-01T00:00:00",
        description="The time the article was published"
    )
    content: str = Field(
        default=...,
        example="Content of the article",
        description="The content of the article"
    )


class NewsWithSummary(News):
    summary: str = Field(
        default=...,
        example="Summary of the article",
        description="The summary of the article"
    )
    reason: str = Field(
        default=...,
        example="Reason of the article",
        description="The reason of the article"
    )


class NewsCrawlerBase(metaclass=abc.ABCMeta):
    news_website_url: AnyHttpUrl | str
    news_website_news_child_urls: list[AnyHttpUrl | str]

    @abc.abstractmethod
    def get_headline(
            self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        """
        Searches for news headlines on the news website based on a given search term and returns a list of headlines.

        This method searches through the entire news_website_url using the specified search term, and returns a list
        of Headline namedtuples, where each Headline includes the title and URL of a news article. The page parameter
        can be an integer representing a single page number or a tuple representing a range of page numbers to search
        through.
        # The offset and limit parameters apply to the resulting list of headlines, allowing you to skip a
        # certain number of headlines and limit the number of headlines returned, respectively.

        :param search_term: A search term to search for news articles.
        :param page: A page number (int) or a tuple of start and end page numbers (tuple[int, int]).
        # :param offset: The number of headlines to skip from the beginning of the list.
        # :param limit: The maximum number of headlines to return.
        :return: A list of Headline namedtuple  s, each containing a title and a URL.
        """
        return NotImplemented

    @abc.abstractmethod
    def parse(self, url: AnyHttpUrl | str) -> News:
        """
        Given a news URL from the news website, fetch and parse the detailed news content.

        This method takes a URL that belongs to a news article on the news_website_url, retrieves the full content of
        the news article, and returns it in the form of a News namedtuple. The News namedtuple includes the title,
        URL, publication time, and content of the news article.

        :param url: The URL of the news article to be fetched and parsed.
        :return: A News namedtuple containing the title, URL, time, and content of the news article.
        """

        return NotImplemented

    def validate_and_parse(self, url: AnyHttpUrl | str) -> News:
        """
        Validates the given URL and ensures that it belongs to the news website or its child URLs. If the URL is valid,
        it proceeds with parsing the news content by invoking the `parse` method from the child class.

        This method first checks if the provided URL is valid for the current news website. If the URL is not valid,
        it raises a `DomainMismatchException`. If the URL is valid, the method passes the URL to the `parse` method
        (which should be implemented in the child class) to retrieve and parse the news content.

        :param url: The URL of the news article to be validated and parsed.
        :return: A `News` object containing the parsed news details (title, URL, time, and content).
        :raises DomainMismatchException: If the URL does not belong to the allowed domain or its child URLs.
        """

        if not self._is_valid_url(url):
            raise DomainMismatchException(url)
        return self.parse(url)


    @staticmethod
    @abc.abstractmethod
    def save(news: News, db: Session | None):
        """
        Save the news content to a persistent storage.

        This method takes a News namedtuple containing the title, URL, publication time, and content of a news article,
        and saves it to a persistent storage, such as a database. The method should handle the storage of the news
        content, ensuring that duplicate news articles are not saved.

        :param news: A News namedtuple containing the title, URL, time, and content of the news article.
        :param db: An instance of the database session to use for saving the news content.
        """
        return NotImplemented

    def _is_valid_url(self, url: AnyHttpUrl | str) -> bool:
        """
        Check if the given URL belongs to the news website or its child URLs.

        This method checks if the given URL belongs to the news_website_url or any of its child URLs. It returns True if
        the URL is valid, and False otherwise.

        :param url: The URL to be checked for validity.
        :return: True if the URL is valid, False otherwise.
        """
        main_domain = tldextract.extract(self.news_website_url).registered_domain
        url_domain = tldextract.extract(url).registered_domain

        if url_domain == main_domain:
            return True
        return False