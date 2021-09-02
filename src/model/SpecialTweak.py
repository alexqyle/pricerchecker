class SpecialTweak(object):
    def __init__(self, cookies: dict[str, str]=None, headers: dict[str, str]=None):
        self.cookies = cookies if cookies else {}
        self.headers = headers if headers else {}

default_headers: dict[str, str] = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
}
