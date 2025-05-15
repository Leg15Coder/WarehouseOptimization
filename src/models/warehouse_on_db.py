import logging
import random
from sqlalchemy.exc import SQLAlchemyError
from collections.abc import Mapping
from typing import Optional, override

from src.exceptions.warehouse_exceptions import FireTooManyWorkersException, EmptyCellException, WarehouseException
from src.models.interfaces.abstract_warehouse import AbstractWarehouse
from src.models.product import Product
from src.models.cell import Cell
from src.models.zone import Zone
from src.models.user import User
from src.models.selection_request import SelectionRequest
from src.parsers.db_parser import db


class Warehouse(AbstractWarehouse):
    def __init__(self):
        logging.debug("Инициализация модели склада")
        self.session = db.session

        self.size = (0, 0)
        self.start_cords = (0, 0)
        self.PROBABILITY_OF_FILLING_CELL = 0.33
        self.MAX_COUNT_TO_ADD_ON_EMPTY_CELL = 64
        self.MAX_COUNT_TO_ADD_ON_NOT_EMPTY_CELL = 16
        self.workers = 1

    def get_all_cells(self) -> list[Cell]:
        return self.session.query(Cell).all()

    def get_cell_by_id(self, cell_id: int) -> Cell:
        return self.session.query(Cell).filter(Cell.cell_id == cell_id).first()

    def get_zones_by_user(self, user_id: int) -> list[Zone]:
        user = self.session.query(User).filter(User.user_id == user_id).first()
        return user.zones if user else []

    def get_all_products(self) -> list[Product]:
        return self.session.query(Product).all()

    def add_product_to_cell(self, cell_id: int, count: int, product_sku: Optional[int] = None) -> bool:
        cell = self.session.query(Cell).filter(Cell.cell_id == cell_id).first()
        if cell:
            if cell.product_sku is None:
                if product_sku is None:
                    raise RuntimeError("Невозможно определить тип товара в ячейке")
                cell.product_sku = product_sku

            cell.count += count
            self.session.commit()
            return True
        return False

    def remove_product_from_cell(self, cell_id: int, count: int) -> bool:
        cell = self.session.query(Cell).filter(Cell.cell_id == cell_id).first()
        if cell and cell.count >= count:
            cell.count -= count

            if cell.count <= 0:
                cell.product_sku = None

            self.session.commit()
            return True
        return False

    def is_moving_cell(self, cell: tuple[int, int]) -> bool:
        x, y = cell
        if x > max(self.size) or y > max(self.size):
            return True

        return any(self.session.query(Cell).filter(Cell.x == x, Cell.y == y))

    def add_workers(self, count: int) -> int:
        """
        Увеличивает количество работников на складе.

        Args:
            count (int): Количество работников для добавления.

        Returns:
            int: Обновленное количество работников.

        Raises:
            ValueError: Если попытаться добавить отрицательное число работников
        """
        if count < 0:
            raise ValueError("Невозможно добавить отрицательное количество работников. Чтобы уволить работников "
                             "используйте Warehouse::remove_workers")

        self.workers += count
        logging.debug(f"Изменено количество работников склада до {self.workers}")
        return self.workers

    def remove_workers(self, count: int) -> int:
        """
        Уменьшает количество работников на складе.

        Args:
            count (int): Количество работников для удаления.

        Returns:
            int: Обновленное количество работников.

        Raises:
            ValueError: Если попытаться удалить отрицательное число работников
            FireTooManyWorkersException: Если пытаются удалить больше работников, чем доступно.
        """
        if count < 0:
            raise ValueError("Невозможно уволить отрицательное количество работников. Чтобы нанять работников "
                             "используйте Warehouse::add_workers")

        if self.workers - count < 0:
            raise FireTooManyWorkersException("Нельзя распустить больше работников, чем имеется")

        self.workers -= count
        logging.debug(f"Изменено количество работников склада до {self.workers}")
        return self.workers

    def generate_new_request(self) -> SelectionRequest:
        """
        Генерирует новый запрос на выборку продуктов случайным образом.

        Returns:
            SelectionRequest: Новый запрос на выборку.

        Raises:
            EmptyListOfProductsException: Если в базе данных нет доступных продуктов.
        """
        products = self.get_all_products()
        if not products:
            raise EmptyListOfProductsException("В базе данных нет ни одного продукта для создания запроса")

        size = random.randint(1, max(0, len(products) - 1))
        result = list()

        for _ in range(size):
            product = random.choice(products)
            products.remove(product)
            result.append((product, random.randint(1, 8)))

        result = SelectionRequest(*result)
        logging.debug(f"Добавлен новый запрос на отбор товаров: {result}")
        return result

    def fill(self) -> None:
        """
        Автоматически заполняет склад продуктами случайным образом.

        Raises:
            EmptyCellException: Если на складе нет ячеек.
        """
        cells = self.get_all_cells()
        logging.debug("Заполнение склада товарами")
        if not all(self.size) or not cells:
            logging.error("Ошибка при заполнении склада")
            raise EmptyCellException("На складе нет ни одной ячейки")

        products = self.get_all_products()

        for cell in cells:
            cell_id, x, y = cell.cell_id, cell.x, cell.y

            if self.PROBABILITY_OF_FILLING_CELL >= random.random():
                if self.is_empty_cell((x, y)):
                    product_sku = random.choice(products)
                    count = random.randint(1, self.MAX_COUNT_TO_ADD_ON_EMPTY_CELL)
                else:
                    product_sku = self.get_type_of_product_on_cell((x, y))
                    count = random.randint(1, self.MAX_COUNT_TO_ADD_ON_NOT_EMPTY_CELL)

                self.add_product_to_cell(cell_id, count, product_sku)

    def build(self, layout: list[list[bool]]) -> None:
        """
        Создает склад на основе переданной карты (layout).

        Args:
            layout (list[list[bool]]): Прямоугольная карта склада, где True - ячейка для складирования, False - проход.

        Raises:
            IllegalSizeException: Если передана пустая или некорректная карта.
            IncompleteMapException: Если карта не имеет прямоугольной формы.
        """
        if not len(layout) or not len(layout[0]):
            logging.error("Невозможно построить склад по заданным параметрам")
            raise IllegalSizeException("Нельзя создать склад с нулём ячеек")
        self.size = (len(layout), len(layout[0]))
        logging.info("Построение модели склада по заданным параметрам")

        with self.session as session:
            try:
                # Удаление всех существующих ячеек
                session.query(Cell).delete()
                session.commit()

                # Заполняем базу данных новыми ячейками
                for x, row in enumerate(layout):
                    if len(row) != self.size[1]:
                        raise IncompleteMapException("Переданная карта ячеек имеет непрямоугольный размер")

                    for y, is_storage_cell in enumerate(row):
                        if is_storage_cell:
                            cell = Cell(x=x, y=y, count=0, product_sku=None, zone_id=None)
                            session.add(cell)

                session.commit()
                logging.info("Склад успешно построен")
            except SQLAlchemyError as e:
                session.rollback()
                logging.error(f"Ошибка при работе с базой данных: {e}")
                raise WarehouseException("Не удалось построить склад из-за ошибки базы данных")

        try:
            self.fill()  # Заполняем склад продуктами
        except WarehouseException:
            logging.error("Ошибка при заполнении склада")

    def is_empty_cell(self, cell: tuple[int, int]) -> bool:
        x, y = cell
        if x > max(self.size) or y > max(self.size):
            return False

        return self.session.query(Cell).filter(Cell.x == x, Cell.y == y).first().count == 0

    def set_start(self, cell: tuple[int, int]) -> None:
        """
        Устанавливает начальную точку для склада.

        Args:
            cell (tuple[int, int]): Координаты начальной точки.

        Raises:
            WrongTypeOfCellException: Если ячейка непригодна для установки начальной точки.
        """
        if self.is_moving_cell(cell):
            logging.info(f"Установлена новая стартовая точка склада (координаты: {cell})")
            self.start_cords = cell
        else:
            logging.warn("Ошибка при попытке установить новую стартовую точку склада")
            raise WrongTypeOfCellException("Даннам координатам соответствует ячейка склада, поэтому невозможно "
                                           "установить начальную позицию")

    def solve(self, request: SelectionRequest) -> Optional[dict]:
        logging.error("Отсутствует реализация алгоритма TSP")
