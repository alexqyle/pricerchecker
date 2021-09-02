import logging
import requests
import time
import traceback
from pyquery import PyQuery
from retry import retry
from model.SpecialTweak import SpecialTweak, default_headers
from model.PriceSelector import PriceSelector

logger = logging.getLogger(__name__)

class Item(object):
    def __init__(self, 
                 name: str, 
                 url: str, 
                 price_selector: PriceSelector, 
                 special_tweak: SpecialTweak=None,
                 get_price_delay: float=0,
                 price: float=None):
        self.name = name
        self.url = url
        self.price_selector = price_selector
        self.special_tweak = special_tweak
        if price:
            self.price = price
            logger.info(f"HardCoded '{self.name}' priced at {self.price}")
        else:
            self.price = self.__get_price(get_price_delay)
            logger.info(f"Fetched '{self.name}' priced at {self.price}")

    def __get_price(self, get_price_delay: float=0) -> float:
        if (get_price_delay > 0):
            time.sleep(get_price_delay)
        headers = default_headers
        cookies = {}
        if self.special_tweak:
            headers = default_headers | self.special_tweak.headers
            cookies = self.special_tweak.cookies
        try:
            return self.__fetch_price(headers, cookies)
        except Exception as error:
            logger.error(f"Unable to get price for '{self.name}'. Error: {error}")
            traceback.print_exc()
            return None

    @retry((Exception), tries=5, delay=5)
    def __fetch_price(self, headers: dict[str, str], cookies: dict[str, str]) -> float:
        req = requests.get(self.url, headers=headers, cookies=cookies, timeout=20)
        html = req.text
        return self.price_selector.scrape_price(PyQuery(html))
