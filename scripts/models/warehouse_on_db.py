import random
from collections.abc import Mapping
from typing import Optional, override

from scripts.exceptions.warehouse_exceptions import FireTooManyWorkersException, EmptyCellException, WarehouseException
from scripts.models.interfaces.abstract_warehouse import AbstractWarehouse
from scripts.models.product import Product
from scripts.models.selection_request import SelectionRequest
from scripts.parsers.db_parser import Database
from scripts.tmp_solve import Graph


class Warehouse(AbstractWarehouse):
    """
    Класс, представляющий склад с ячейками, продуктами и рабочими.
    Реализует методы для управления продуктами, рабочими, запросами,
    а также взаимодействие с базой данных.

    Атрибуты:
        db (Database): Объект для работы с базой данных склада.
        size (tuple[int, int]): Размеры склада (строки, столбцы).
        start_cords (tuple[int, int]): Начальные координаты (для определенных задач, если требуется).
        PROBABILITY_OF_FILLING_CELL (float): Вероятность заполнения ячейки при автозаполнении.
        MAX_COUNT_TO_ADD_ON_EMPTY_CELL (int): Максимальное количество продуктов для добавления в пустую ячейку.
        MAX_COUNT_TO_ADD_ON_NOT_EMPTY_CELL (int): Максимальное количество продуктов для добавления в непустую ячейку.
        workers (int): Количество работников на складе.
    """

    def __init__(self):
        self.db = Database()
        self.size = (0, 0)
        self.start_cords = (0, 0)
        self.PROBABILITY_OF_FILLING_CELL = 0.33
        self.MAX_COUNT_TO_ADD_ON_EMPTY_CELL = 64
        self.MAX_COUNT_TO_ADD_ON_NOT_EMPTY_CELL = 16
        self.workers = 1

    def __get_cell(self, cell: tuple[int, int]) -> Optional[int]:
        """
        Получает идентификатор ячейки в базе данных по её координатам.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            Optional[int]: Идентификатор ячейки или None, если ячейка не найдена.
        """
        x, y = cell
        result = self.db.get_by_prompt(
            f"SELECT id FROM Cells WHERE x={x} AND y={y}"
        )
        return result[0][0] if result else None

    def __get_all_from_cell(self, cell: tuple[int, int]) -> Optional[tuple]:
        """
        Получает всю информацию о продуктах из ячейки.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            Optional[tuple]: Данные о продуктах в ячейке или None, если ячейка пуста.
        """
        result = self.db.get_by_prompt(
            f"SELECT * FROM Warehouse WHERE cell_id={self.__get_cell(cell)}"
        )
        return result[0] if result else None

    def __get_all_from_cell_as_dict(self, cell: tuple[int, int]) -> dict:
        """
        Получает продукты в ячейке в виде множества.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            set: Множество с объектами продуктов и их количеством.
        """
        result = dict()
        product = self.__get_all_from_cell(cell)

        if product:
            _, sku, count, __ = product

            product = self.db.get_by_prompt(
                f"SELECT * FROM Products WHERE sku={sku}"
            )
            product = Product(*product[0])

            result[product] = result.get(product, 0) + count
        return result

    @override
    def get_type_of_product_on_cell(self, cell: tuple[int, int]) -> Product:
        """
        Получает тип продукта в указанной ячейке.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            Product: Продукт в ячейке.

        Raises:
            EmptyCellException: Если ячейка пуста.
        """
        result = self.__get_all_from_cell(cell)

        if not result:
            raise EmptyCellException("На данной ячейке ничего не лежит")

        sku = result[1]
        product = self.db.get_by_prompt(
            f"SELECT * FROM Products WHERE sku={sku}"
        )[0]
        return Product(*product)

    @override
    def check_type_of_product_on_cell(self, cell: tuple[int, int], product: Product) -> bool:
        """
        Проверяет, соответствует ли продукт в указанной ячейке заданному типу.

        Args:
            cell (tuple[int, int]): Координаты ячейки.
            product (Product): Продукт для проверки.

        Returns:
            bool: True, если продукт совпадает, иначе False.
        """
        return product.sku == self.get_type_of_product_on_cell(cell).sku

    @override
    def is_moving_cell(self, cell: tuple[int, int]) -> bool:
        """
        Проверяет, является ли ячейка доступной для передвижения персоналу.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            bool: True, если ячейка перемещаемая, иначе False.
        """
        x, y = cell
        if x > max(self.size) or y > max(self.size):
            return True

        result = self.__get_cell(cell)
        return not result

    @override
    def remove_product_from_cell(self, count: int, cell: tuple[int, int]) -> None:
        """
        Удаляет заданное количество продукта из указанной ячейки.

        Args:
            count (int): Количество продукта для удаления.
            cell (tuple[int, int]): Координаты ячейки.

        Raises:
            EmptyCellException: Если ячейка пуста.
        """
        cell_id = self.__get_cell(cell)
        cur_products = self.__get_all_from_cell_as_dict(cell)

        if not cur_products:
            raise EmptyCellException("Нельзя удалить продукты из пустой ячейки.")

        # Удаляем все продукты из ячейки
        self.db.execute(
            f"DELETE FROM Warehouse WHERE cell_id={cell_id}"
        )

        # Перезаписываем оставшиеся продукты после удаления
        for product in cur_products:
            if cur_products[product] - count >= 0:
                cur_products[product] -= count

            if cur_products[product] > 0:
                self.db.execute(
                    '''
                    INSERT INTO Warehouse (sku, count, cell_id) VALUES (?, ?, ?)
                    ''',
                    params=(product.sku, cur_products[product], cell_id)
                )

    @override
    def add_product_to_cell(self, count: int, cell: tuple[int, int], product=None) -> None:
        """
        Добавляет продукт в указанную ячейку.

        Args:
            count (int): Количество продукта для добавления.
            cell (tuple[int, int]): Координаты ячейки.
            product (Product): Продукт для добавления.

        Raises:
            WarehouseException: Если ячейка не существует.
        """
        cell_id = self.__get_cell(cell)
        if not cell_id:
            raise WarehouseException("Ячейка не существует.")

        cur_products = self.__get_all_from_cell_as_dict(cell)

        # Удаляем все текущие данные из ячейки
        self.db.execute(
            f"DELETE FROM Warehouse WHERE cell_id={cell_id}"
        )

        # Обновляем данные о продуктах
        cur_products[product] = cur_products.get(product, 0)
        cur_products[product] += count

        # Вставляем обновленные данные обратно
        self.db.execute(
            '''
            INSERT INTO Warehouse (sku, count, cell_id) VALUES (?, ?, ?)
            ''',
            params=(product.sku, cur_products[product], cell_id)
        )

    @override
    def add_workers(self, count: int) -> int:
        """
        Увеличивает количество работников на складе.

        Args:
            count (int): Количество работников для добавления.

        Returns:
            int: Обновленное количество работников.
        """
        self.workers += count
        return self.workers

    @override
    def remove_workers(self, count: int) -> int:
        """
        Уменьшает количество работников на складе.

        Args:
            count (int): Количество работников для удаления.

        Returns:
            int: Обновленное количество работников.

        Raises:
            FireTooManyWorkersException: Если пытаются удалить больше работников, чем доступно.
        """
        if self.workers - count < 0:
            raise FireTooManyWorkersException("Нельзя распустить больше работников, чем имеется")

        self.workers -= count
        return self.workers

    @override
    def generate_new_request(self) -> SelectionRequest:
        """
        Генерирует новый запрос на выборку продуктов случайным образом.

        Returns:
            SelectionRequest: Новый запрос на выборку.

        Raises:
            EmptyListOfProductsException: Если в базе данных нет доступных продуктов.
        """
        products = self.db.get_all_products()
        if not products:
            raise EmptyListOfProductsException("В базе данных нет ни одного продукта для создания запроса")

        products = [Product(*p) for p in products]
        size = random.randint(1, max(1, len(products) // 2))
        result = list()

        for _ in range(size):
            product = random.choice(products)
            products.remove(product)
            result.append((product, random.randint(1, 10)))

        return SelectionRequest(*result)

    @override
    def fill(self) -> None:
        """
        Автоматически заполняет склад продуктами случайным образом.

        Raises:
            EmptyCellException: Если на складе нет ячеек.
        """
        cells = self.db.get_all_cells()
        if not all(self.size) or not cells:
            raise EmptyCellException("На складе нет ни одной ячейки")

        products = self.db.get_all_products()
        products = [p[0] for p in products]

        for cell in cells:
            cell_id, x, y = cell

            if self.PROBABILITY_OF_FILLING_CELL >= random.random():
                if self.is_empty_cell((x, y)):
                    product_sku = random.choice(products)
                    count = random.randint(1, self.MAX_COUNT_TO_ADD_ON_EMPTY_CELL)
                else:
                    product_sku = self.get_type_of_product_on_cell((x, y))
                    count = random.randint(1, self.MAX_COUNT_TO_ADD_ON_NOT_EMPTY_CELL)

                self.db.execute(
                    '''
                    INSERT INTO Warehouse (sku, count, cell_id) VALUES (?, ?, ?)
                    ''',
                    params=(product_sku, count, cell_id)
                )

    @override
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
            raise IllegalSizeException("Нельзя создать склад с нулём ячеек")
        self.size = (len(layout), len(layout[0]))

        # Удаляем старые данные
        self.db.execute("DELETE FROM Warehouse")
        self.db.execute("DELETE FROM Cells")

        # Заполняем базу данных новыми ячейками
        for x in range(self.size[0]):
            if len(layout[x]) != self.size[1]:
                raise IncompleteMapException("Переданная карта ячеек имеет непрямоугольный размер")

            for y in range(self.size[1]):
                if layout[x][y]:
                    self.db.cursor.execute(
                        "INSERT INTO Cells (x, y) VALUES (?, ?)",
                        (x, y)
                    )
        self.db.connection.commit()

        try:
            self.fill()  # Заполняем склад продуктами
        except WarehouseException:
            print("Ошибка при заполнении склада")

    @override
    def is_empty_cell(self, cell: tuple[int, int]) -> bool:
        """
        Проверяет, пуста ли указанная ячейка.

        Args:
            cell (tuple[int, int]): Координаты ячейки.

        Returns:
            bool: True, если ячейка пуста, иначе False.
        """
        cell_id = self.__get_cell(cell)
        connections_with_cell = self.db.get_by_prompt(
            f"SELECT * FROM Warehouse WHERE cell_id={cell_id}"
        )
        return not connections_with_cell

    def set_start(self, cell: tuple[int, int]) -> None:
        """
        Устанавливает начальную точку для склада.

        Args:
            cell (tuple[int, int]): Координаты начальной точки.

        Raises:
            WrongTypeOfCellException: Если ячейка непригодна для установки начальной точки.
        """
        if self.is_moving_cell(cell):
            self.start_cords = cell
        else:
            raise WrongTypeOfCellException("Даннам координатам соответствует ячейка склада, поэтому невозможно "
                                           "установить начальную позицию")

    @override
    def solve(self, request: SelectionRequest) -> Optional[dict]:  # todo on C++
        result = Graph(self).solve(request)
        return result if result is None else {'cells': result}
