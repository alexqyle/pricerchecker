import gspread
import logging
import os.path
import traceback
from datetime import datetime
from google.oauth2 import service_account
from gspread.models import Spreadsheet, Worksheet
from gspread.utils import absolute_range_name, rowcol_to_a1
from retry import retry
from exporter.DataExporter import DataExporter
from model.Item import Item
from model.ItemGroup import ItemGroup

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

class GoogleSheetExporter(DataExporter):
    def __init__(self, service_account_key_file: str, spreadsheet_id: str):
        if not os.path.isfile(service_account_key_file):
            message = f"Service Account key file does not exist: {service_account_key_file}"
            logger.error(message)
            raise Exception(message)
        self.service_account_key_file = service_account_key_file
        self.spreadsheet_id = spreadsheet_id
        self.insert_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def exportor_info(self) -> str:
        return f"Google sheet exporter with spreadsheet id: {self.spreadsheet_id}"

    def export_data(self, item_groups: list[ItemGroup]) -> None:
        try:
            self.spreadsheet = self.__load_spreadsheet()
            logger.info(f"Loaded Google Sheet: {self.spreadsheet.title}")
        except Exception as error:
            logger.error(f"Unable to load spreadsheet with id: {self.spreadsheet_id}. Error: {error}")
            raise error
        try:
            all_sheets = self.__load_all_worksheets(self.spreadsheet)
        except Exception as error:
            logger.error(f"Unable to load worksheets in Google sheet: {self.spreadsheet.title}. Error: {error}")
            raise error

        for item_group in item_groups:
            group_name = item_group.group_name
            items = item_group.items
            if group_name in all_sheets:
                self.sheet = all_sheets[group_name]
            else:
                try:
                    self.sheet = self.__create_new_worksheet(self.spreadsheet, group_name)
                    logger.info(f"Created new worksheet with title: {group_name}")
                except Exception as error:
                    logger.error(f"Unable to create new worksheet with title: {group_name}. Error: {error}")
                    traceback.print_exc()
                    continue
            try:
                item_index_dict = {}
                if self.__get_col_count(self.sheet) > 1:
                    labels = self.__row_values(self.sheet, 1)
                    item_index_dict = {value: i + 1 for i, value in enumerate(labels)}
                self.sheet = self.__update_labels(self.sheet, items, item_index_dict)
                self.sheet = self.__insert_new_data(self.sheet, items, item_index_dict)
                logger.info(f"Finished exporting data to worksheet: {self.sheet.title} in Google Sheet: {self.spreadsheet.title}")
            except Exception as error:
                logger.error(f"Unable to export data to worksheet: {self.sheet.title} in Google Sheet: {self.spreadsheet.title}. Error: {error}")
                traceback.print_exc()
                continue
        logger.info(f"Finished exporting data to Google Sheet: {self.spreadsheet.title}")

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __load_spreadsheet(self) -> Spreadsheet:
        credentials = service_account.Credentials.from_service_account_file(self.service_account_key_file, scopes=SCOPES)
        gspread_client = gspread.authorize(credentials)
        return gspread_client.open_by_key(self.spreadsheet_id)

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __load_all_worksheets(self, spreadsheet: Spreadsheet) -> list[Worksheet]:
        return {sheet.title: sheet for sheet in spreadsheet.worksheets()}

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __create_new_worksheet(self, spreadsheet: Spreadsheet, sheet_title: str) -> Worksheet:
        return self.spreadsheet.add_worksheet(title=sheet_title, rows="10000", cols="50")

    def __insert_new_data(self, sheet: Worksheet, items: list[Item], item_index_dict: dict[str, int]) -> Worksheet:
        col_number = self.__get_col_count(sheet)
        new_row = [''] * col_number
        new_row[0] = self.insert_time
        for item in items:
            item_col = item_index_dict[item.name]
            new_row[item_col - 1] = item.price
        row_number = self.__get_row_count(sheet) + 1
        cell_to_insert = rowcol_to_a1(row_number, 1)
        sheet.append_row(new_row, value_input_option='USER_ENTERED', table_range=cell_to_insert)
        logger.info(f"Inserted new data row: {new_row} at cell: {cell_to_insert} in worksheet: {sheet.title}")
        self.__format_date_cell(sheet, row_number, 1)
        self.__format_currency_cells(sheet, row_number, 2, row_number, col_number)
        return sheet

    def __update_labels(self, sheet: Worksheet, items: list[Item], item_index_dict: dict[str, int]) -> Worksheet:
        new_labels = []
        col_number = self.__get_col_count(sheet)
        if col_number == 0:
            sheet.update_cell(1, 1, '-')
            col_number += 1
        col_start = col_number + 1
        col_number = col_start
        for item in items:
            item_name = item.name
            if not item_name in item_index_dict:
                item_index_dict[item_name] = col_number
                new_labels.append(item_name)
                col_number += 1
        if len(new_labels) == 0:
            return sheet
        cell_to_insert = rowcol_to_a1(1, col_start)
        sheet.append_row(new_labels, value_input_option='USER_ENTERED', table_range=cell_to_insert)
        logger.info(f"Created new labels: {new_labels} at cell: {cell_to_insert} in worksheet: {sheet.title}")
        return sheet

    def __get_row_count(self, sheet: Worksheet) -> int:
        raw_values = self.__col_values(sheet, 1)
        values = self.__remove_trailing_none_values(raw_values)
        row_count = len(values)
        if row_count == sheet.row_count - 100:
            try:
                self.__create_rows(sheet, 10000)
                self.sheet = self.__refresh_sheet(self.spreadsheet, sheet)
            except Exception as error:
                logger.warn(f"Unable to create new rows: {error}")
                pass
        return row_count

    def __get_col_count(self, sheet: Worksheet) -> int:
        raw_values = self.__row_values(sheet, 1)
        values = self.__remove_trailing_none_values(raw_values)
        col_count = len(values)
        if col_count == sheet.col_count - 20:
            try:
                self.__create_cols(sheet, 50)
                self.sheet = self.__refresh_sheet(self.spreadsheet, sheet)
            except Exception as error:
                logger.warn(f"Unable to create new columns: {error}")
                pass
        return col_count

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __row_values(self, sheet: Worksheet, row_num: int) -> list[object]:
        try:
            return sheet.row_values(row_num)
        except IndexError:
            return []

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __col_values(self, sheet: Worksheet, col_num: int) -> list[object]:
        return sheet.col_values(col_num)

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __create_rows(self, sheet: Worksheet, rows: int) -> None:
        sheet.add_rows(rows)

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __create_cols(self, sheet: Worksheet, cols: int) -> None:
        sheet.add_cols(cols)

    def __remove_trailing_none_values(self, values):
        while values and values[-1] is None:
            values.pop()
        return values

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __refresh_sheet(self, spreadsheet: Spreadsheet, sheet: Worksheet) -> Worksheet:
        return spreadsheet.get_worksheet_by_id(sheet.id)

    def __format_date_cell(self, sheet: Worksheet, row: int, col: int) -> None:
        self.__format_date_cells(sheet, row, col, row, col)

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __format_date_cells(self, sheet: Worksheet, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        cell_range = self.__cast_to_a1_notation(start_row, start_col, end_row, end_col)
        sheet.format(cell_range, {
            'numberFormat': {
                'type': 'DATE_TIME'
            }
        })

    def __format_currency_cell(self, sheet: Worksheet, row: int, col: int) -> None:
        self.__format_currency_cells(sheet, row, col, row, col)

    @retry((Exception), tries=5, delay=1, backoff=2)
    def __format_currency_cells(self, sheet: Worksheet, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        cell_range = self.__cast_to_a1_notation(start_row, start_col, end_row, end_col)
        sheet.format(cell_range, {
            'numberFormat': {
                'type': 'CURRENCY'
            }
        })

    def __cast_to_a1_notation(self, start_row: int, start_col: int, end_row: int, end_col: int) -> str: 
        range_start = rowcol_to_a1(start_row, start_col)
        range_end = rowcol_to_a1(end_row,end_col )
        return ':'.join((range_start, range_end))
