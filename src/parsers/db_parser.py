import os
from subprocess import run
import logging
import psycopg2
import shutil
from datetime import datetime

from src.models.product import Product
from src.parsers.config_parser import config


class Database(object):
    """
    Класс Database представляет интерфейс для работы с базой данных склада.
    Реализует подключение к PostgreSQL, управление таблицами и выполнение запросов.
    """

    def __init__(self):
        """
        Инициализация подключения к базе данных.
        Создаёт соединение с базой данных по указанному пути и инициализирует таблицы, если их ещё нет.
        """
        logging.debug("Подключение к БД")

        try:
            self.connection = psycopg2.connect(
                dbname=config.dbname.get_secret_value(),
                user=config.dbuser.get_secret_value(),
                password=config.dbpassword.get_secret_value(),
                host=config.dbhost.get_secret_value(),
                port=config.dbport.get_secret_value()
            )
            self.cursor = self.connection.cursor()
        except OperationalError | OSError as e:
            logging.error(f"Не удалось подключиться к БД: {e}")
            raise ConnectionError(f"Не удалось подключиться к БД: {e}")

        self.init_tables()

    def __del__(self):
        """
        Завершение работы с базой данных.
        Выполняет сохранение (commit) изменений и закрывает соединение.
        """
        self.connection.commit()
        self.connection.close()

    def __commit(self):
        """
        Приватный метод для сохранения изменений в базе данных.
        """
        self.connection.commit()

    def execute(self, prompt: str, params=()) -> None:
        """
        Выполняет SQL-запрос без возврата результата.

        :param prompt: Строка SQL-запроса.
        :param params: Параметры для безопасной подстановки в запрос.
        """
        self.cursor.execute(prompt, params)
        self.__commit()

    def get_by_prompt(self, prompt: str, params=()) -> tuple:
        """
        Выполняет SQL-запрос (SELECT) и возвращает все результаты.

        :param prompt: Строка SQL-запроса.
        :param params: Параметры для безопасной подстановки в запрос.
        :return: Кортеж с результатами выполнения запроса.
        """
        return self.cursor.execute(prompt, params).fetchall()

    def init_tables(self) -> None:
        """
        Создаёт таблицы базы данных, если они ещё не существуют:
        """
        logging.debug("Проверка данных в БД на корректность")
        with open(r"db/migrations/V1__create_tables.sql", 'r') as file:
            self.execute(file.read())

        with open(r"db/migrations/V1__add_constraints.sql", 'r') as file:
            self.execute(file.read())

    def get_all_cells(self) -> tuple:
        """
        Возвращает все записи из таблицы Cells.

        :return: Кортеж с информацией обо всех ячейках склада.
        """
        return self.get_by_prompt("SELECT * FROM cell")

    def get_all_products(self) -> tuple:
        """
        Возвращает все записи из таблицы Products.

        :return: Кортеж с информацией обо всех продуктах.
        """
        return self.get_by_prompt("SELECT * FROM product")

    def create_product_type(self, product: Product) -> None:
        """
        Добавляет новый тип продукта в таблицу Products.

        :param product: Объект Product, представляющий добавляемый продукт.
        """
        product_type = 'NONETYPE' if product.product_type is None else product.product_type
        self.execute(
            '''
            INSERT INTO product (product_sku, time_to_select, time_to_ship, max_amount, product_type) VALUES (?, ?, ?)
            ''',
            params=(product.sku, product.time_to_select, product.time_to_ship, product.max_amount, product_type)
        )

    async def backup(self):
        """
        Создаёт SQL-бэкап базы данных в указанную папку.
        Требует установленный pg_dump (PostgreSQL CLI).
        """
        logging.info("Начало сохранения бэкапа БД")
        path = "db/backups"

        os.makedirs(path, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(path, f"backup_{timestamp}.sql")

        command = [
            "pg_dump",
            "-h", self.connection.info.host,
            "-p", str(self.connection.info.port),
            "-U", self.connection.info.user,
            "-d", self.connection.info.dbname,
            "-f", backup_file
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = self.connection.info.password

        logging.info(f"Создание бэкапа: {backup_file}")
        result = run(command, env=env)

        if result.returncode != 0:
            logging.error("Ошибка при создании бэкапа БД")
            raise RuntimeError("Ошибка при создании бэкапа")

        logging.info("Бэкап успешно сохранён")
