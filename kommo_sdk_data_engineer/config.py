from pydantic import AnyHttpUrl


class KommoConfig:
    _instance = None

    def __new__(cls, url_company: AnyHttpUrl=None, token_long_duration: str=None, limit_request_per_second: int = 6):
        if cls._instance is None:
            cls._instance = super(KommoConfig, cls).__new__(cls)
            cls._instance.url_company = url_company
            cls._instance.token_long_duration = token_long_duration
            cls._instance.limit_request_per_second = limit_request_per_second
        return cls._instance
