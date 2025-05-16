import asyncio
import logging

import websockets
import json
import random
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from src.parsers.json_parser import ParserManager
from src.exceptions.json_parser_exceptions import ExecutionError

# Хранение подключённых клиентов
connected_clients = set()
# Инициализация менеджера для обработки JSON-запросов
manager = ParserManager()


async def server_handler(websocket: ServerConnection) -> None:
    """
    Обрабатывает подключение WebSocket-клиента.

    :param websocket: Объект подключения клиента.
    """
    connected_clients.add(websocket)  # Добавляем клиента в список подключённых
    logging.info(f"Клиент {websocket.id} подключился")
    # Запуск фоновой задачи для отправки статуса сервера клиенту
    # asyncio.create_task(send_server_status(websocket))

    try:
        # Чтение сообщений от клиента
        async for message in websocket:
            # Парсинг JSON-сообщения
            data = json.loads(message)

            try:
                data['websocket'] = websocket
                await manager.execute(data)
                logging.info(f"Сервер принял сообщение {data}")
            except Exception as e:
                logging.warn(f"Ошибка обработки на стороне сервера {e}")
                response = {
                    "type": "answer",
                    "status": "Internal Server Error",
                    "code": 500,
                    "message": str(e)
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


async def send_server_status(websocket: ServerConnection) -> None:
    """
    Периодически отправляет клиенту обновлённое состояние сервера.

    :param websocket: Объект подключения клиента.
    """
    while True:
        try:
            # Выполнение запроса для получения данных сервера
            data = await manager.execute({"type": "solve"})

            if data is None:
                await asyncio.sleep(0.1)
                continue

            # Формирование и отправка сообщения клиенту
            message = {
                "type": "server_update",
                "body": data
            }
            await websocket.send(json.dumps(message))
            logging.debug(f"Сервер отправил сообщение {message}")

        except ConnectionClosed:
            logging.info(f"Клиент {websocket.id} отключился")
            break
        except Exception as e:
            # Логирование ошибок при отправке сообщения
            logging.error(f"Ошибка при отправке сообщения: {e}")
        await asyncio.sleep(0.5)
