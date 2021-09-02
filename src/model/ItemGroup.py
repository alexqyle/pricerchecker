from model.Item import Item


class ItemGroup(object):
    def __init__(self, group_name: str, items: list[Item]=None):
        self.group_name = group_name
        self.items = items if items else []

    def add(self, item: Item) -> None:
        self.items.append(item)

    def add_all(self, items: list[Item]) -> None:
        self.items.extend(items)
