from typing import Optional

from src.models.product import Product
from src.models.selection_request import SelectionRequest


class AbstractWarehouse(object):
    """
    Абстрактный класс склада. Этот класс определяет основные методы и свойства,
    необходимые для управления складом. Класс включает в себя методы для работы с ячейками,
    продуктами, запросами и персоналом.

    Атрибуты:
        size (tuple[int, int]): Размер склада в формате (количество строк, количество столбцов).
    """

    size: tuple[int, int]

    def get_type_of_product_on_cell(self, cell: tuple[int, int]) -> Product:
        """
        Получает тип продукта, находящегося в указанной ячейке.

        Args:
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).

        Returns:
            Product: Тип продукта в указанной ячейке.
        """
        pass

    def check_type_of_product_on_cell(self, cell: tuple[int, int], product: Product) -> bool:
        """
        Проверяет, соответствует ли продукт в указанной ячейке заданному типу.

        Args:
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).
            product (Product): Продукт, с которым необходимо сравнить содержимое ячейки.

        Returns:
            bool: True, если тип продукта совпадает, иначе False.
        """
        pass

    def is_moving_cell(self, cell: tuple[int, int]) -> bool:
        """
        Проверяет, является ли указанная доступной для передвижения персоналу.

        Args:
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).

        Returns:
            bool: True, если является, иначе False.
        """
        pass

    def remove_product_from_cell(self, count: int, cell: tuple[int, int]) -> None:
        """
        Удаляет указанное количество продуктов из ячейки.

        Args:
            count (int): Количество удаляемых продуктов.
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).

        Returns:
            None
        """
        pass

    def add_product_to_cell(self, count: int, cell: tuple[int, int], product=None) -> None:
        """
        Добавляет указанное количество продуктов в ячейку.

        Args:
            count (int): Количество добавляемых продуктов.
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).
            product (Optional[Product]): Тип продукта (по умолчанию None).

        Returns:
            None
        """
        pass

    def add_workers(self, count: int) -> int:
        """
        Добавляет указанное количество работников на склад.

        Args:
            count (int): Количество добавляемых работников.

        Returns:
            int: Текущее количество работников после добавления.
        """
        pass

    def add_worker(self) -> int:
        """
        Добавляет одного работника на склад.

        Returns:
            int: Текущее количество работников после добавления.
        """
        return self.add_workers(1)

    def remove_workers(self, count: int) -> int:
        """
        Удаляет указанное количество работников со склада.

        Args:
            count (int): Количество удаляемых работников.

        Returns:
            int: Текущее количество работников после удаления.
        """
        pass

    def remove_worker(self) -> int:
        """
        Удаляет одного работника со склада.

        Returns:
            int: Текущее количество работников после удаления.
        """
        return self.remove_workers(1)

    def generate_new_request(self) -> SelectionRequest:
        """
        Генерирует новый запрос на выборку продуктов.

        Returns:
            SelectionRequest: Новый запрос.
        """
        pass

    def fill(self) -> None:
        """
        Заполняет склад начальными продуктами или ресурсами.

        Returns:
            None
        """
        pass

    def build(self, layout) -> None:
        """
        Строит склад на основе переданной схемы.

        Args:
            layout: Схема склада. Значение True на схеме означает ячейку хранения.

        Returns:
            None
        """
        pass

    def is_empty_cell(self, cell: tuple[int, int]) -> bool:
        """
        Проверяет, является ли указанная ячейка пустой.

        Args:
            cell (tuple[int, int]): Координаты ячейки (строка, столбец).

        Returns:
            bool: True, если ячейка пустая, иначе False.
        """
        pass

    def solve(self, request: SelectionRequest) -> Optional[list]:
        """
        Обрабатывает запрос на выборку продуктов.

        Args:
            request (SelectionRequest): Запрос на выборку продуктов.

        Returns:
            Optional[list]: Список действий для выполнения запроса или None, если запрос оставили в обработке.
        """
        pass
