import csv
import logging
import traceback
import shutil
from datetime import datetime
from pathlib import Path
from retry import retry
from exporter.DataExporter import DataExporter
from model.Item import Item
from model.ItemGroup import ItemGroup

logger = logging.getLogger(__name__)

class CsvExporter(DataExporter):
    def __init__(self, csv_dir: Path):
        super().__init__()
        self.csv_dir = csv_dir
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.insert_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def exportor_info(self) -> str:
        return f"CSV exporter exports all data to directory: {self.csv_dir.absolute()}"

    def export_data(self, item_groups: list[ItemGroup]) -> None:
        for item_group in item_groups:
            try:
                item_group_name = item_group.group_name
                items = item_group.items
                item_headers = [i.name for i in items]
                item_group_csv_file = self.csv_dir.joinpath(f"{item_group_name}.csv")
                new_item_group_csv_file = self.csv_dir.joinpath(f"{item_group_name}.csv.tmp")
                if not new_item_group_csv_file.exists():
                    new_item_group_csv_file.open('x').close()
                if not item_group_csv_file.exists():
                    all_rows = []
                else:
                    with item_group_csv_file.open('r', newline='') as csv_file:
                        reader = csv.reader(csv_file)
                        all_rows = [row for row in reader]
                if not all_rows:
                    item_headers.insert(0, 'Date')
                    item_prices = [self.insert_time]
                    item_prices.extend([i.price for i in items])
                    all_rows.append(item_headers)
                    logger.info(f"Added new headers: {item_headers}")
                    all_rows.append(item_prices)
                    logger.info(f"Added new row: {item_prices}")
                else:
                    headers = all_rows[0]
                    new_headers = [h for h in item_headers if h not in headers]
                    headers.extend(new_headers)
                    logger.info(f"Added new headers: {new_headers}")
                    item_price_dict = {item.name: item.price for item in items}
                    new_row = [self.insert_time]
                    for header in headers[1:]:
                        new_row.append(item_price_dict.get(header, None))
                    all_rows.append(new_row)
                    logger.info(f"Added new row: {new_row}")
                self.__write_to_csv(new_item_group_csv_file, all_rows)
                shutil.move(new_item_group_csv_file, item_group_csv_file)
                logger.info(f"Finished exporting data to csv file: {item_group_csv_file.absolute()}")
            except Exception as error:
                    logger.error(f"Unable to export data to csv file: {item_group_csv_file.absolute()}. Error: {error}")
                    traceback.print_exc()
                    new_item_group_csv_file.unlink(missing_ok=True)
                    continue
        logger.info(f"Finished exporting data to csv files under directory: {self.csv_dir.absolute()}")

    @retry((Exception), tries=5, delay=1)
    def __write_to_csv(self, csv_file_path: Path, all_rows: list[list[str]]) -> None:
        with csv_file_path.open('w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for row in all_rows:
                writer.writerow(row)
