import argparse
import logging
import pathlib
import traceback
from app.PriceCheckerConfig import PriceCheckerConfig
from exporter.GoogleSheetExporter import GoogleSheetExporter

def __parse_args():
    parser = argparse.ArgumentParser(description='Price Checker')
    parser.add_argument('--config', dest='config_file', type=pathlib.Path, required=True, help='Config file to be used')
    return parser.parse_args()

def main():
    logger = logging.getLogger(__name__)

    args = __parse_args()
    with args.config_file.open('r') as config_file:
        config = PriceCheckerConfig(config_file)
    for data_exporter in config.data_exporters:
        try:
            data_exporter.export_data(config.item_groups)
        except Exception as error:
            logger.error(f"Unable to export data for exporter: {data_exporter.exportor_info()}. Error: {error}")
            traceback.print_exc()
            continue

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(module)s.%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    main()
