import asyncio
import threading
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue


class SizeType(Enum):
    TINY = 1
    SMALL = 2
    MEDIUM = 3
    LARGE = 4
    EXTRA_LARGE = 5


class Algorithm:
    warehouse: Warehouse
    clusters_controller: Clusterizer
    size_type: SizeType

    requests_queue: PriorityQueue[SelectionRequest]
    deadline_checker = None
    products_stack: dict[Product, int]

    deadline_flag: bool = False
    full_stack_flag: bool = False
    one_product_left_flag: bool = False

    def __init__(self):
        self.warehouse = Warehouse()
        self.clusters_controller = Clusterizer(self.warehouse)
        self.size_type = self.clusters_controller.analyze()

        self.requests_queue = PriorityQueue()
        self.products_stack = dict()

        threading.Thread(target=self.check_flags, daemon=True).start()

    def check_flags(self):
        threading.Thread(target=self._watch_flags_loop, daemon=True).start()
        threading.Thread(target=self._watch_one_product_left, daemon=True).start()
        threading.Thread(target=self._schedule_deadline_check, daemon=True).start()

        while True:
            if self.deadline_flag or self.full_stack_flag or self.one_product_left_flag:
                pass

    def _watch_flags_loop(self):
        while True:
            for product, count in self.products_stack.items():
                if count >= product.max_per_hand:
                    self.full_stack_flag = True
            asyncio.sleep(1)

    def _watch_one_product_left(self):
        while True:
            for request in self.requests_queue:
                remaining = self._remaining_products(request)
                if len(remaining) == 1:
                    self.one_product_left_flag = True
            asyncio.sleep(1)

    def _schedule_deadline_check(self):
        oldest_request: SelectionRequest = None
        deadline_time: time = None

        while True:
            top_request: SelectionRequest = self.requests_queue.queue[0]
            if top_request is not oldest_request:
                oldest_request = top_request
                deadline_time = deadline_time - timedelta(seconds=5)
            if datetime.now() - datetime <= 0:
                self.deadline_flag = True
            asyncio.sleep(1)

    async def solve(self, request: SelectionRequest) -> Optional[str]:
        pass

    async def choose_clusters(self, request: SelectionRequest) -> list[Cluster]:
        pass

    async def choose_cells(self, clusters: list[Cluster]) -> set[int]:
        pass

    async def build_way(self, cells: set[int]) -> list[int]:
        pass
