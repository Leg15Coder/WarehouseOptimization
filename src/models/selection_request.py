from typing import Iterable

from src.exceptions.selection_exceptions import UnsupportedFormat, BadInstance
from src.models.product import Product


class SelectionRequest(object):
    """
    Класс, представляющий запрос на выборку продуктов со склада.

    Атрибуты:
        data (dict): Словарь, содержащий продукты и их количество.
            Ключ - объект класса Product, значение - количество.
    """

    def __init__(self, *args):
        """
        Инициализирует объект запроса на выборку продуктов.

        Args:
            *args: Список кортежей, где каждый кортеж состоит из объекта Product
                и количества этого продукта (int).

        Пример:
            request = SelectionRequest((product1, 5), (product2, 10))
        """
        self.data = dict()  # Словарь для хранения продуктов и их количества.
        self.add_products_from_list(args)

    def __ior__(self, other):
        for product, count in other.items():
            self.data[product] = self.data.get(product, 0) + count
        return self

    def __or__(self, other):
        data = self.data.copy()
        for product, count in other.items():
            self.data[product] = self.data.get(product, 0) + count
        return SelectionRequest(*((key, data[key]) for key in data))

    def __sub__(self, other):
        data = self.data.copy()
        for product, count in other.items():
            if product in data:
                data[product] -= count
                if data[product] <= 0:
                    del data[product]
        return SelectionRequest(*((key, data[key]) for key in data))

    def __isub__(self, other):
        for product, count in other.items():
            if product in self.data:
                self.data[product] -= count
                if self.data[product] <= 0:
                    del self.data[product]
        return self

    def __iter__(self):
        return self.data

    def __bool__(self):
        return bool(self.data)

    def __str__(self):
        return str(self.data)

    def add_products_from_list(self, products: Iterable) -> None:
        """
        Добавляет продукты в запрос из списка кортежей.

        Args:
            products (list[tuple[Product, int]]): Список кортежей, где каждый
                кортеж состоит из объекта Product и количества этого продукта.

        Raises:
            UnsupportedFormat: Если переданный элемент списка не является кортежем.
            UnsupportedFormat: Если кортеж не содержит ровно два элемента.
            BadInstance: Если первый элемент кортежа не является объектом Product.
            BadInstance: Если второй элемент кортежа не является int.

        Пример:
            request.add_products_from_list([(product1, 3), (product2, 7)])
        """
        for element in products:
            if not isinstance(element, tuple):  # Проверка, что элемент - кортеж.
                raise UnsupportedFormat("Элемент должен быть кортежем.")
            if len(element) != 2:  # Проверка, что кортеж состоит из двух элементов.
                raise UnsupportedFormat("Кортеж должен содержать ровно два элемента.")
            if not isinstance(element[0], Product):  # Проверка, что первый элемент - Product.
                raise BadInstance("Первый элемент кортежа должен быть объектом Product.")
            if not isinstance(element[1], int):  # Проверка, что второй элемент - int.
                raise BadInstance("Второй элемент кортежа должен быть целым числом.")

            # Извлечение продукта и количества из кортежа.
            product, count = element
            # Добавление продукта в словарь или увеличение его количества.
            self.data[product] = self.data.setdefault(product, 0) + count

    def get_data(self) -> tuple:
        """
        Возвращает данные запроса в виде кортежа.

        Returns:
            tuple: Кортеж, содержащий пары (Product, количество) из запроса.

        Пример:
            data = request.get_data()
            # Вернет что-то вроде: ((product1, 5), (product2, 10))
        """
        return tuple((key, self.data[key]) for key in self.data)

    def to_dict_like_json(self) -> dict:
        return {'request': {key.sku: self.data[key] for key in self.data}}

    def items(self):
        return self.data.items()
