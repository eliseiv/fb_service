import threading

from app.infrastructure.schemas import FacebookItem


class ItemTracker:
    """
    A class to track processed items in a microservice.
    """

    __processed_items: set[str] = set()
    __to_insert: list[FacebookItem] = []

    def __init__(self):
        self.lock = threading.Lock()

    def processed(self, web: str) -> bool:
        """
        Add an item to the processed items set.

        :param web: The item to add.
        """
        if web in self.__processed_items:
            return True
        with self.lock:
            self.__processed_items.add(web)
        return False

    def add(self, item: FacebookItem) -> None:
        """
        Add an item to the to_insert list.

        :param item: The item to add.
        """
        with self.lock:
            self.__to_insert.append(item)

    def get(self):
        """
        Get the list of items to insert.

        :return: The list of items to insert.
        """
        with self.lock:
            items = self.__to_insert.copy()
            self.__to_insert.clear()
        return items

    def clear(self):
        """
        Clear all tracked data.
        """
        with self.lock:
            self.__processed_items.clear()
            self.__to_insert.clear()


tracker = ItemTracker()