import os
from subprocess import run
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import shutil
from datetime import datetime

from src.server.base import Base
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
            dbname = config.dbname.get_secret_value()
            user = config.dbuser.get_secret_value()
            password = config.dbpassword.get_secret_value()
            host = config.dbhost.get_secret_value()
            port = config.dbport.get_secret_value()
            url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

            self.engine = create_engine(url, future=True)
            self.session = scoped_session(sessionmaker(bind=self.engine))
            self.base = Base
            logging.debug("БД успешно подключена")
        except OperationalError | OSError as e:
            logging.error(f"Не удалось подключиться к БД: {e}")
            raise ConnectionError(f"Не удалось подключиться к БД: {e}")

        self.init_tables()

    def __del__(self):
        """
        Завершение работы с базой данных.
        Выполняет сохранение (commit) изменений и закрывает соединение.
        """
        self.__commit()

    def __commit(self):
        """
        Приватный метод для сохранения изменений в базе данных.
        """
        self.session.commit()

    def init_tables(self):
        """Создаёт все таблицы в базе данных, если они ещё не существуют."""
        logging.debug("Проверка данных в БД")
        logging.debug("Создание таблиц")
        self.base.metadata.create_all(self.engine)
        names = (
            'V1__create_tables.sql',
            'V2__add_constraints.sql',
            'V3__add_triggers.sql'
        )

        with self.engine.connect() as connection:
            for f in names:
                with open(rf'db/migrations/{f}', 'r', encoding='utf-8') as file:
                    logging.debug(f"Выполнение миграции из {f}")
                    connection.exec_driver_sql(file.read())
        logging.debug("Проверка выполнена успешно")


db = Database()
