import logging
import random
import asyncio
import websockets
import socket

import src.logging.logger
from src.models.product import Product
from src.models.warehouse_on_db import Warehouse
from src.server.server import server_handler
from src.parsers.json_parser import manager


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.0.255", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as ex:
        return "127.0.0.1"


async def main():
    logging.debug("Инициализация сервера")
    server = await websockets.serve(server_handler, "0.0.0.0", 8765)
    local_ip = get_local_ip()
    logging.info(f"Сервер запущен на ws://{local_ip}:8765")

    await manager.warehouse.solver.start()
    logging.info("Алгоритм инициализирован")

    await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
