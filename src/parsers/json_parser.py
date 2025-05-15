import json
import logging
from typing import Optional

from src.exceptions.json_parser_exceptions import ExecutionError
from src.models.warehouse_on_db import Warehouse


class ParserManager(object):
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
        self.warehouse = Warehouse()
        self.namespase = {
            "solve": solve,
            "warehouse_map": build_map,
            "answer": do_nothing,
            "update_map": do_nothing,
            "update_workers": do_nothing,
            "get_status": send_current_requests
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
            args[0] = self.warehouse  # Добавление объекта склада в качестве первого аргумента
            return self.namespase[item](*args, **kwargs)
        else:
            raise KeyError("Неизвестный протокол обмена")

    def __getitem__(self, item: str):
        """
        Возвращает функцию, соответствующую указанному типу команды.

        :param item: Тип команды.
        :return: Функция из `namespase`.
        :raises KeyError: Если команда неизвестна.
        """
        if item in self.namespase:
            logging.debug(f"Запрос на выполнение задачи {self.namespase[item]}")
            return self.namespase[item]
        else:
            logging.warn("Неизвестный протокол обмена на уровне парсера")
            raise KeyError("Неизвестный протокол обмена")

    def execute(self, data: dict) -> None:
        """
        Выполняет указанную команду на основе переданных данных.

        :param data: Словарь с данными, содержащий тип команды (`type`) и дополнительные параметры.
        :return: Результат выполнения команды.
        :raises ExecutionError: Если данные команды некорректны.
        """
        if not isinstance(data, dict) or 'type' not in data:
            raise ExecutionError("Ошибка обработки команды")
        return self(data['type'], data)


async def do_nothing(*args, **kwargs) -> None:
    """
    Функция-заглушка, которая ничего не делает.

    :param args: Список аргументов.
    :param kwargs: Словарь дополнительных параметров.
    """
    pass


async def build_map(warehouse: Warehouse, data: dict) -> None:
    """
    Создаёт карту склада на основе переданных данных.

    :param warehouse: Объект склада.
    :param data: Словарь с данными, содержащий карту склада под ключом `map`.
    """
    warehouse.build(data["map"])


async def solve(warehouse: Warehouse, data=None) -> Optional[dict]:
    request = warehouse.generate_new_request()
    result = warehouse.solve(request)
    result['selection'] = request.to_dict_like_json()
    return result


async def send_current_requests(warehouse: Warehouse, data: dict) -> None:
    response = dict()
    websocket = data['websocket']
    count = data['requests_count']
    response['type'] = 'selections'
    response['body'] = list()
    for _ in range(count):
        response['body'].append(await solve(warehouse))
    await websocket.send(json.dumps(response))
