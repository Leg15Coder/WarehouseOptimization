import logging
import sqlite3 as sql
from src.models.product import Product


class Database(object):
    """
    Класс Database представляет интерфейс для работы с базой данных склада.
    Реализует подключение к SQLite, управление таблицами и выполнение запросов.
    """

    def __init__(self):
        """
        Инициализация подключения к базе данных.
        Создаёт соединение с базой данных по указанному пути и инициализирует таблицы, если их ещё нет.
        """
        logging.debug("Подключение к БД")
        self.connection = sql.connect('db/db.db')
        self.cursor = self.connection.cursor()
        self.init_tables()

    def __del__(self):
        """
        Завершение работы с базой данных.
        Выполняет сохранение (commit) изменений и закрывает соединение.
        """
        self.connection.commit()
        self.connection.close()

    def execute(self, prompt: str, params=()) -> None:
        """
        Выполняет SQL-запрос без возврата результата.

        :param prompt: Строка SQL-запроса.
        :param params: Параметры для безопасной подстановки в запрос.
        """
        self.cursor.execute(prompt, params)
        self.__commit()

    def get_by_prompt(self, prompt: str) -> tuple:
        """
        Выполняет SQL-запрос (SELECT) и возвращает все результаты.

        :param prompt: Строка SQL-запроса.
        :return: Кортеж с результатами выполнения запроса.
        """
        return self.cursor.execute(prompt).fetchall()

    def init_tables(self) -> None:
        """
        Создаёт таблицы базы данных, если они ещё не существуют:
        - Cells: хранит информацию о ячейках склада.
        - Products: хранит информацию о продуктах.
        - Warehouse: связывает продукты с ячейками склада и их количеством.
        """
        logging.debug("Проверка данных в БД на корректность")
        self.execute(
            '''
            CREATE TABLE IF NOT EXISTS Cells (
            id INTEGER PRIMARY KEY,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL
            )
            '''
        )
        self.execute(
            '''
            CREATE TABLE IF NOT EXISTS Products (
            sku INTEGER PRIMARY KEY,
            time_to_select REAL NOT NULL,
            time_to_ship REAL NOT NULL
            )
            '''
        )
        self.execute(
            '''
            CREATE TABLE IF NOT EXISTS Warehouse (
            id INTEGER PRIMARY KEY,
            sku INTEGER NOT NULL,
            count INTEGER NOT NULL,
            cell_id INTEGER NOT NULL,
            FOREIGN KEY (sku) REFERENCES Products (sku),
            FOREIGN KEY (cell_id) REFERENCES Cells (id)
            )
            '''
        )

    def get_all_cells(self) -> tuple:
        """
        Возвращает все записи из таблицы Cells.

        :return: Кортеж с информацией обо всех ячейках склада.
        """
        return self.get_by_prompt(
            '''
            SELECT * FROM Cells
            '''
        )

    def get_all_products(self) -> tuple:
        """
        Возвращает все записи из таблицы Products.

        :return: Кортеж с информацией обо всех продуктах.
        """
        return self.get_by_prompt(
            '''
            SELECT * FROM Products
            '''
        )

    def __commit(self):
        """
        Приватный метод для сохранения изменений в базе данных.
        """
        self.connection.commit()

    def create_product_type(self, product: Product) -> None:
        """
        Добавляет новый тип продукта в таблицу Products.

        :param product: Объект Product, представляющий добавляемый продукт.
        """
        self.execute(
            '''
            INSERT INTO Products (sku, time_to_select, time_to_ship) VALUES (?, ?, ?)
            ''',
            params=(product.sku, product.time_to_select, product.time_to_ship)
        )
