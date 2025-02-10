from pydantic import AnyHttpUrl


class KommoConfig:
    def __init__(self, url_company: AnyHttpUrl, token_long_duration: str, limit_request_per_second: int = 6):
        self.url_company = url_company
        self.token_long_duration = token_long_duration
        self.limit_request_per_second = limit_request_per_second
