import logging
import random
import asyncio
import websockets
import socket

from scripts.models.product import Product
from scripts.models.warehouse_on_db import Warehouse
from scripts.server.server import server_handler


async def main():
    file_log = logging.FileHandler("logs/app.log", "w")
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(file_log, console_out), level=logging.DEBUG, encoding='utf-8')

    logging.debug("Инициализация сервера")
    server = await websockets.serve(server_handler, "0.0.0.0", 8765)
    local_ip = socket.gethostbyname(socket.gethostname())
    logging.info(f"Сервер запущен на ws://{local_ip}:8765")

    await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
