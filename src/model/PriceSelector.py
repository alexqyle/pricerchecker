import logging
import re
from pyquery import PyQuery

logger = logging.getLogger(__name__)

class PriceSelector(object):
    def __init__(self, 
                 full_price_selector: str=None, 
                 decimal_integer_selector: str=None, 
                 decimal_fraction_selector: str=None, 
                 is_euro: bool=False):
        self.full_price_selector = full_price_selector
        self.decimal_integer_selector = decimal_integer_selector
        self.decimal_fraction_selector = decimal_fraction_selector
        self.decimal_point = ',' if is_euro else '.'
        self.number_dilemma = '.' if is_euro else ','
        if not self.full_price_selector:
            if not self.decimal_integer_selector or not self.decimal_fraction_selector:
                message = 'If full_price_selector is not provided, both decimal_integer_selector and decimal_fraction_selector should be provided.'
                logger.error(message)
                raise Exception(message)
        else:
            if self.decimal_integer_selector or self.decimal_fraction_selector:
                message = 'If full_price_selector is provided, both decimal_integer_selector and decimal_fraction_selector should not be provided.'
                logger.error(message)
                raise Exception(message)

    def scrape_price(self, py_query: PyQuery) -> float:
        if self.full_price_selector:
            price_text = self.__scrape_number_text(py_query, self.full_price_selector)
            return float(price_text)
        else:
            integer_text = self.__scrape_number_text(py_query, self.decimal_integer_selector)
            fraction_text = self.__scrape_number_text(py_query, self.decimal_fraction_selector)
            return float(f"{integer_text}.{fraction_text}")

    def __scrape_number_text(self, py_query: PyQuery, selector: str) -> str:
        number_text = py_query(selector).eq(0).text()
        return self.__clean_up_price_text(number_text)

    def __clean_up_price_text(self, price_text: str) -> str:
        cleaned = price_text
        cleaned = re.sub(r'(^.*?)(\d)', r'\g<2>', cleaned)
        cleaned = re.sub(r'[^\d]+$', '', cleaned)
        return cleaned.replace(self.number_dilemma, '')
