from pandas.io.sql import execute


class Product(object):
    """
    Класс, представляющий продукт на складе.
    """

    def __init__(self, sku: int, time_to_select: float, time_to_ship: float, max_amount: int = 1, product_type=None, **kwargs):
        """
        Инициализирует объект продукта.

        Args:
            sku (int): Уникальный идентификатор товара (артикул).
            time_to_select (float): Время на выбор товара.
            time_to_ship (float): Время на отгрузку товара.
            max_amount (int): Максимальное количество данного товара в одной ячейке.
            product_type (Optional[str]): Категория товара.
            **kwargs: Дополнительные параметры продукта.
        """
        self.sku = sku
        self.time_to_select = time_to_select
        self.time_to_ship = time_to_ship
        self.limits = dict(kwargs)
        self.max_amount = max_amount
        self.product_type = product_type

    def check_limits(self) -> None:
        """
        Проверяет, соблюдаются ли ограничения товара.

        Метод может быть реализован для проверки дополнительных параметров,
        таких как максимальный вес, объем или иные свойства товара.

        Returns:
            None
        """
        pass

    def __str__(self):
        """
        Возвращает строковое представление товара (артикул).

        Returns:
            str: Артикул продукта.
        """
        return str(self.sku)

    def __repr__(self):
        """
        Возвращает строковое представление товара для целей отладки.

        Returns:
            str: Артикул продукта.
        """
        return self.__str__()
