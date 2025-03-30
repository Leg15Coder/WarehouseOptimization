class Product(object):
    """
    Класс, представляющий продукт на складе.

    Атрибуты:
        sku (int): Уникальный идентификатор продукта (артикул).
        time_to_select (float): Время, необходимое для выбора продукта со склада (в секундах или минутах).
        time_to_ship (float): Время, необходимое для отгрузки продукта (в секундах или минутах).
        limits (dict): Дополнительные ограничения или параметры продукта.
    """

    def __init__(self, sku: int, time_to_select: float, time_to_ship: float, **kwargs):
        """
        Инициализирует объект продукта.

        Args:
            sku (int): Уникальный идентификатор продукта (артикул).
            time_to_select (float): Время на выбор продукта.
            time_to_ship (float): Время на отгрузку продукта.
            **kwargs: Дополнительные параметры продукта.
        """
        self.sku = sku
        self.time_to_select = time_to_select
        self.time_to_ship = time_to_ship
        self.limits = dict(kwargs)

    def check_limits(self) -> None:
        """
        Проверяет, соблюдаются ли ограничения продукта.

        Метод может быть реализован для проверки дополнительных параметров,
        таких как максимальный вес, объем или иные свойства продукта.

        Returns:
            None
        """
        pass

    def __str__(self):
        """
        Возвращает строковое представление продукта (артикул).

        Returns:
            str: Артикул продукта.
        """
        return str(self.sku)

    def __repr__(self):
        """
        Возвращает строковое представление продукта для целей отладки.

        Returns:
            str: Артикул продукта.
        """
        return self.__str__()
