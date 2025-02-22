import logging
import random
import asyncio
import websockets

from scripts.models.product import Product
from scripts.models.warehouse_on_db import Warehouse
from scripts.server.server import server_handler


async def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    logging.debug("Инициализация сервера")
    server = await websockets.serve(server_handler, "0.0.0.0", 8765)
    logging.INFO("Сервер запущен на ws://0.0.0.0:8765")
    await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
