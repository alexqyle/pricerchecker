from abc import ABC, abstractmethod
from model.ItemGroup import ItemGroup

class DataExporter(ABC):

    @abstractmethod
    def export_data(self, item_groups: list[ItemGroup]) -> None:
        pass
