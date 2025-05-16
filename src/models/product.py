from pandas.io.sql import execute
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from src.parsers.db_parser import db


class Product(db.base):
    """
    Класс, представляющий продукт на складе.
    """
    __tablename__ = 'product'

    sku = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    time_to_select = Column(Float, nullable=False)
    time_to_ship = Column(Float, nullable=False)
    max_amount = Column(Integer)
    product_type = Column(String)

    cells = relationship('Cell', back_populates='product')

    def check_limits(self) -> bool:
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
