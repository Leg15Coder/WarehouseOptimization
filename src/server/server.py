import asyncio
import logging

import websockets
import json
import random
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from src.parsers.json_parser import manager
from src.exceptions.parser_exceptions import ExecutionError
from src.parsers.config_parser import config

# Хранение подключённых клиентов
connected_clients = set()


async def server_handler(websocket: ServerConnection) -> None:
    """
    Обрабатывает подключение WebSocket-клиента.

    :param websocket: Объект подключения клиента.
    """
    connected_clients.add(websocket)  # Добавляем клиента в список подключённых
    logging.info(f"Клиент {websocket.id} подключился")
    # Запуск фоновой задачи для отправки статуса сервера клиенту
    asyncio.create_task(send_request(websocket))

    try:
        # Чтение сообщений от клиента
        async for message in websocket:
            # Парсинг JSON-сообщения
            data = json.loads(message)
            logging.info(f"Сервер принял сообщение")

            if 'auth' not in data or data['auth'] != config.wsauth.get_secret_value():
                await websocket.send(json.dumps(
                    {
                        "type": "response",
                        "code": 401,
                        "status": "error",
                        "message": "Не авторизован"
                    }
                ))
                continue

            try:
                if 'type' not in data:
                    await websocket.send(json.dumps(
                        {
                            "type": "response",
                            "code": 100,
                            "status": "ok"
                        }
                    ))
                    continue

                data['websocket'] = websocket
                response = await manager.execute(data)
                if response is not None:
                    await websocket.send(json.dumps(response))
                logging.debug("Сервер ответил")
            except Exception as e:
                logging.error(f"Ошибка обработки на стороне сервера {e}")
                response = {
                    "type": "answer",
                    "status": "error",
                    "code": 500,
                    "message": "Фатальная ошибка на стороне сервера"
                }
                await websocket.send(json.dumps(response))

    except ConnectionClosed:
        # Обработка ситуации, когда клиент разорвал соединение
        logging.warn(f"Клиент {websocket.id} отключился до завершения сессии")
    except Exception as e:
        logging.error(f"Ошибка обработки запроса: {e}")
    finally:
        # Удаляем клиента из списка подключённых
        connected_clients.remove(websocket)


async def send_request(websocket: ServerConnection) -> None:
    """
    Периодически отправляет клиенту обновлённое состояние сервера.

    :param websocket: Объект подключения клиента.
    """
    while True:
        try:
            # Выполнение запроса для получения данных сервера
            data = await manager.execute({"type": "run"})

            if data is None or not data:
                await asyncio.sleep(1)
                continue

            # Формирование и отправка сообщения клиенту
            message = {
                "type": "request",
                "message": "Неофициальный результат тестирования",
                "data": {
                    "worker_id": "UNDEFINED",
                    "moving_cells": [data],
                }
            }
            await websocket.send(json.dumps(message))
            logging.debug(f"Сервер отправил сообщение клиенту {websocket.id}")

        except ConnectionClosed:
            logging.info(f"Клиент {websocket.id} отключился")
            break
        except Exception as e:
            # Логирование ошибок при отправке сообщения
            logging.error(f"Ошибка при отправке сообщения: {e}")
        finally:
            await asyncio.sleep(0.5)
