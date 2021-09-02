import logging
import yaml
from typing import IO, Any
from exporter.DataExporter import DataExporter
from exporter.GoogleSheetExporter import GoogleSheetExporter
from model.Item import Item
from model.ItemGroup import ItemGroup
from model.PriceSelector import PriceSelector
from model.SpecialTweak import SpecialTweak

logger = logging.getLogger(__name__)

class PriceCheckerConfig(object):
    def __init__(self, config_file: IO[Any]):
        self.price_selectors: dict[str, PriceSelector] = {}
        self.special_tweaks: dict[str, SpecialTweak] = {}
        self.item_groups: list[ItemGroup] = []
        self.data_exporters: list[DataExporter] = []
        self.__parse_config(config_file)

    def __parse_config(self, config_file: IO[Any]) -> None:
        config = yaml.safe_load(config_file)
        for price_selector_yaml in config['price_selectors']:
            self.price_selectors[price_selector_yaml['selector_name']] = PriceSelector(
                full_price_selector=price_selector_yaml.get('full_price_selector', None),
                decimal_integer_selector=price_selector_yaml.get('decimal_integer_selector', None),
                decimal_fraction_selector=price_selector_yaml.get('decimal_fraction_selector', None)
            )
        for special_tweak_yaml in config['special_tweaks']:
            self.special_tweaks[special_tweak_yaml['tweak_name']] = SpecialTweak(
                cookies=special_tweak_yaml.get('cookies', None),
                headers=special_tweak_yaml.get('headers', None)
            )
        for item_group_yaml in config['item_groups']:
            item_group_name = item_group_yaml['group_name']
            if 'disabled' in item_group_yaml and item_group_yaml['disabled']:
                logger.warn(f"Skip item group: {item_group_name}")
            else:
                item_group = ItemGroup(item_group_name)
                for item_yaml in item_group_yaml['items']:
                    item_name = item_yaml['name']
                    if 'disabled' in item_yaml and item_yaml['disabled']:
                        logger.warn(f"Skip item: {item_name} in item group: {item_group_name}")
                    else:
                        item_group.add(
                            Item(
                                name=item_name,
                                url=item_yaml['url'],
                                price_selector=self.price_selectors[item_yaml['price_selector']],
                                special_tweak=self.special_tweaks[item_yaml['special_tweak']] if 'special_tweak' in item_yaml else None,
                                get_price_delay=item_yaml.get('get_price_delay', 0),
                                price=item_yaml.get('price', None))
                        )
                self.item_groups.append(item_group)
        for data_exporter in config.get('data_exporters', []):
            type = data_exporter['type']
            if type == 'google_sheet':
                exporter = GoogleSheetExporter(data_exporter['google_service_account_key_file'], data_exporter['spreadsheet_id'])
            else:
                message = f"Unsupported data exporter type: {type}"
                logger.error(message)
                raise Exception(message)
            self.data_exporters.append(exporter)
