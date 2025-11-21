class DomainMismatchException(Exception):
    """Exception raised for URLs whose domain does not match the news website's domain."""

    def __init__(
        self,
        url: str,
        message: str = "URL's domain does not match the news website's domain",
    ):
        self.url = url
        self.message = message
        super().__init__(self.message)