from pydantic import AnyHttpUrl


class KommoConfig:
    '''
    Class to store the configuration of the Kommo API.

    :param url_company: The base URL of the Kommo API.
    :type url_company: AnyHttpUrl

    :param token_long_duration: The token of the user with long duration.
    :type token_long_duration: str

    :param limit_request_per_second: The limit of requests per second. Defaults to 6, maximum is 6.
    :type limit_request_per_second: int
    '''
    def __init__(self, url_company: AnyHttpUrl, token_long_duration: str, limit_request_per_second: int = 6):
        self.url_company = url_company
        self.token_long_duration = token_long_duration
        self.limit_request_per_second = limit_request_per_second
