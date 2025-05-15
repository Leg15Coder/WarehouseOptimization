import os
from subprocess import run
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import shutil
from datetime import datetime

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

            self.engine = create_engine(url)
            self.session = scoped_session(sessionmaker(bind=self.engine))
            self.base = declarative_base()
            logging.debug("БД успешно подключена")
        except OperationalError | OSError as e:
            logging.error(f"Не удалось подключиться к БД: {e}")
            raise ConnectionError(f"Не удалось подключиться к БД: {e}")

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
        self.base.metadata.create_all(self.engine)


db = Database()
