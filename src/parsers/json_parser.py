import json
import logging

from src.algorithm.app import Algorithm
from src.exceptions.parser_exceptions import ExecutionError
from src.exceptions.warehouse_exceptions import EmptyListOfProductsException, IllegalSizeException
from src.models.product import Product
from src.models.warehouse_on_db import Warehouse
from src.parsers.db_parser import db


class ParserManager:
    """
    Класс для управления парсингом входящих команд и их выполнения на складе.

    Атрибуты:
        warehouse (Warehouse): Объект склада, с которым осуществляется взаимодействие.
        namespase (dict): Словарь функций, соответствующих типам запросов.
    """

    def __init__(self):
        """
        Инициализирует объект ParserManager, создавая склад и определяя список поддерживаемых команд.
        """
        logging.debug("Инициализация парсера данных формата JSON")
        self.warehouse = Warehouse(Algorithm())
        self.namespase = {
            "create_warehouse": build_map,
            "server_status": do_nothing,
            "create_product_type": create_product,
            "delete_product_type": delete_product,
            "list_product_types": product_list,
            "worker_free_report": do_nothing,
            "update_warehouse": do_nothing,
            "run": solve
        }

    def __call__(self, *args, **kwargs):
        """
        Вызывает соответствующую функцию из `namespase` в зависимости от переданного типа команды.

        :param args: Список аргументов.
        :param kwargs: Словарь дополнительных параметров.
        :return: Результат выполнения соответствующей команды.
        :raises KeyError: Если команда неизвестна.
        """
        args = list(args)
        if not args or args[0] in self.namespase:
            item = args[0]  # Тип команды
            args = args[1:]
            return self.namespase[item](*args, **kwargs)
        else:
            raise KeyError("Неизвестный протокол обмена")

    def __getitem__(self, item: str):
        if item in self.namespase:
            logging.debug(f"Запрос на выполнение задачи {self.namespase[item]}")
            return self.namespase[item]
        else:
            logging.warn("Неизвестный протокол обмена на уровне парсера")
            return undefined_function

    def execute(self, data: dict) -> None:
        """
        Выполняет указанную команду на основе переданных данных.

        :param data: Словарь с данными, содержащий тип команды (`type`) и дополнительные параметры.
        :return: Результат выполнения команды.
        :raises ExecutionError: Если данные команды некорректны.
        """
        data['warehouse'] = self.warehouse
        if not isinstance(data, dict) or 'type' not in data:
            raise ExecutionError("Ошибка обработки команды")
        return self(data['type'], data)


async def do_nothing(*args, **kwargs) -> dict:
    return {
        "type": "response",
        "code": 501,
        "status": "error",
        "message": "Не реализовано"
    }


async def undefined_function(*args, **kwargs) -> dict:
    return {
        "type": "response",
        "code": 418,
        "status": "error",
        "message": "Я не могу заварить вам кофе, потому что я чайник"
    }


async def build_map(data: dict) -> dict:
    try:
        if 'payload' not in data or 'layout' not in data['payload']:
            raise ValueError()
        data = data['payload']
        warehouse = data['warehouse']

        warehouse.build(data["layout"])

        if 'add_workers' in data:
            warehouse.add_workers(data['add_workers'])
        if 'remove_workers' in data:
            warehouse.remove_workers(data['remove_workers'])
        if 'workers_count' in data:
            warehouse.set_workers(data['workers_count'])

        if 'filling_rules' in data:
            data = data['filling_rules']

            if 'empty_cell_ratio' in data:
                warehouse.EMPTY_CELL_RATIO = float(data['empty_cell_ratio'])
            if 'heavily_filled_ratio' in data:
                warehouse.HEAVILY_FILLED_RATIO = float(data['heavily_filled_ratio'])

        return {
            "type": "response",
            "code": 201,
            "status": "ok",
            "message": "Склад успешно создан и предзаполнен товарами"
        }
    except EmptyListOfProductsException:
        return {
            "type": "response",
            "code": 400,
            "status": "error",
            "message": "Перед созданием склада необходимо создать хранимые товары"
        }
    except IllegalSizeException:
        return {
            "type": "response",
            "code": 400,
            "status": "error",
            "message": "Некорректные размеры склада"
        }
    except ValueError:
        return {
            "type": "response",
            "code": 400,
            "status": "error",
            "message": "Некорректный формат запроса"
        }


async def create_product(data: dict) -> dict:
    try:
        if 'payload' not in data:
            raise ValueError()
        data = data['payload']
        skus = list()

        for product in data['payload']:
            if 'sku' not in product or not isinstance(product['sku'], int):
                raise ValueError()
            sku = product['sku']
            name = product['name'] if 'name' in product else f'PRODUCT{sku}'
            time_to_select = product['time_to_select'] if 'time_to_select' in product else 1
            time_to_ship = product['time_to_ship'] if 'time_to_ship' in product else 1
            max_amount = product['max_amount'] if 'max_amount' in product else 64
            product_type = product['product_type'] if 'product_type' in product else None

            with db.session() as session:
                try:
                    product = Product(
                        sku=sku,
                        name=name,
                        time_to_select=time_to_select,
                        time_to_ship=time_to_ship,
                        max_amount=max_amount,
                        product_type=product_type
                    )

                    session.add(product)
                    session.commit()
                    skus.append(sku)
                except SQLAlchemyError:
                    session.rollback()

        return {
            "type": "response",
            "code": 201,
            "status": "ok",
            "message": f"Созданы товары с артикулами {skus}"
        }
    except ValueError:
        return {
            "type": "response",
            "code": 400,
            "status": "error",
            "message": "Некорректный формат запроса"
        }


async def delete_product(data: dict) -> dict:
    try:
        if 'payload' not in data:
            raise ValueError()
        data = data['payload']
        skus = list()

        if 'skus' not in data['payload']:
            raise ValueError()
        for sku in skus:
            if not isinstance(sku, int):
                raise ValueError()
            sku = product['sku']

            with db.session() as session:
                try:
                    session.query(Product).filter(Product.sku == sku).delete()
                    session.commit()
                    skus.append(sku)
                except SQLAlchemyError:
                    session.rollback()

        return {
            "type": "response",
            "code": 202,
            "status": "ok",
            "message": f"Удалены товары с артикулами {skus}"
        }
    except ValueError:
        return {
            "type": "response",
            "code": 400,
            "status": "error",
            "message": "Некорректный формат запроса"
        }


async def product_list(data: dict) -> dict:
    products = db.session.query(Product).all()
    products = list(map(lambda x: x.__dict__, products))
    return {
        "type": "response",
        "code": 200,
        "status": "ok",
        "message": f"Найдено {len(products)} различных типов товаров",
        "data": {
            products
        }
    }


async def solve(data: dict) -> dict:
    warehouse = data['warehouse']
    request = warehouse.generate_new_request()
    return {
      "type": "response",
      "code": 103,
      "status": "ok",
      "data": {
          "result": warehouse.solve(request)
      }
    }
