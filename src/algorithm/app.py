import asyncio
from queue import PriorityQueue as SyncPriorityQueue
from asyncio import PriorityQueue
import threading
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from src.algorithm.genetic import GeneticAlgorithm
from src.algorithm.utils import run_async_thread, AsyncThreadLocker
from src.models.cell import Cell
from src.models.warehouse_on_db import Warehouse
from src.models.selection_request import SelectionRequest
from src.models.product import Product
from src.algorithm.clusterizer import Clusterizer, Cluster
from src.algorithm.size_enum import SizeType
from src.algorithm.optimiser import adapter


class ProductWrapper:
    def __init__(self, count: int = 0, nearest_deadline: Optional[datetime] = None):
        self.count = count
        self.deadlines = SyncPriorityQueue()
        if nearest_deadline is not None:
            self.deadlines.put(nearest_deadline)

    def push_deadline(self, deadline: Optional[datetime]):
        if deadline is not None:
            self.deadlines.put(deadline)

    def nearest_deadline(self):
        if self.deadlines.queue:
            return self.deadlines.queue[0]
        return None

    def pop_deadline(self):
        if self.nearest_deadline() is not None:
            return self.deadlines.get()


executor__ = ThreadPoolExecutor(max_workers=256)


class Algorithm:
    class __FlagContainer:
        def __init__(self):
            self.flag = False
            self.request = SelectionRequest()

        def __ior__(self, other: SelectionRequest):
            self.request |= other
            return self

        def __isub__(self, other: SelectionRequest):
            self.request -= other
            return self

        def __invert__(self):
            self.flag = not self.flag
            return self

        def __pos__(self):
            self.flag = True
            return self

        def __neg__(self):
            self.flag = False
            return self

        def __bool__(self):
            return self.flag

        def __iter__(self):
            return ((product, self.request[product]) for product in self.request)

    warehouse: Warehouse
    clusters_controller: Clusterizer
    size_type: SizeType

    requests_queue: PriorityQueue[SelectionRequest]
    requests_in_wait: dict[Product, ProductWrapper]
    requests_in_process: dict[Product, int]
    outbox_container: list

    deadline_flag: __FlagContainer = __FlagContainer()
    full_stack_flag: __FlagContainer = __FlagContainer()
    one_product_left_flag: __FlagContainer = __FlagContainer()

    locker: AsyncThreadLocker = AsyncThreadLocker(asyncio.Lock(), threading.Lock())
    thread_locker: threading.Lock = threading.Lock()
    async_locker: asyncio.Lock = asyncio.Lock()
    _stop_event: threading.Event
    __threads: list[threading.Thread] = list()
    _async_task: asyncio.Task

    def __init__(self):
        self.warehouse = Warehouse(self)
        self.clusters_controller = Clusterizer(self.warehouse)

        self.requests_queue = PriorityQueue()
        self.requests_in_wait = dict()
        self.requests_in_process = dict()
        self.outbox_container = list()

        self._stop_event = threading.Event()

    async def start(self):
        self._async_task = asyncio.create_task(self.run_process())
        self.size_type = await self.clusters_controller.analyze()

    def __del__(self):
        self._stop_event.set()

        if hasattr(self, '_async_task'):
            self._async_task.cancel()

        executor__.shutdown(wait=False)

        for thread in self.__threads:
            if thread.is_alive():
                thread.join(timeout=1)

    async def solve(self, request: Optional[SelectionRequest]) -> Optional[list[int]]:
        with self.thread_locker:
            async with self.async_locker:
                if request is None:
                    request = SelectionRequest()

                while self.requests_queue._queue and not self.requests_queue._queue[0]:
                    await self.requests_queue.get()

                await self.requests_queue.put(request)

                for product, count in request.items():
                    deadline = datetime.now() + timedelta(seconds=10)
                    tmp = self.requests_in_wait.get(product, ProductWrapper(0, None))
                    tmp.count += count
                    self.requests_in_wait[product] = tmp
                    self.requests_in_wait[product].push_deadline(deadline)

                if bool(self.outbox_container):
                    res = self.outbox_container[0]
                    self.outbox_container = self.outbox_container[1:]
                    return res

    async def run_process(self):
        self._run_thread(self._watch_max_stack)
        self._run_thread(self._watch_one_product_left)
        self._run_thread(self._schedule_deadline_check)
        self._run_thread(self._answer_requests)

        while True:
            await self.check_flags_and_run()
            await asyncio.sleep(0.1)

    def _watch_max_stack(self):
        while True:
            local_flag = False
            for product, wrapper in self.requests_in_wait.items():
                if not self.full_stack_flag and wrapper.count >= product.max_per_hand:
                    self.full_stack_flag |= SelectionRequest((product, wrapper.count))
                    local_flag = True

            if local_flag:
                self.full_stack_flag = +self.full_stack_flag
            time.sleep(1)

    def _watch_one_product_left(self):
        while True:
            break  # todo later
            local_flag = False
            for request in self.requests_queue:
                if abs(request) == 1:  # Остался последний товар
                    self.one_product_left_flag |= request
                    local_flag = True

            if local_flag:
                self.one_product_left_flag = +self.one_product_left_flag
            time.sleep(1)

    def _schedule_deadline_check(self):
        while True:
            local_flag = False

            for product, wrapper in self.requests_in_wait.items():
                if (not self.deadline_flag and wrapper.nearest_deadline() is not None and wrapper.count > 0
                        and wrapper.nearest_deadline() - timedelta(seconds=5) <= datetime.now()):
                    self.deadline_flag |= SelectionRequest((product, wrapper.count))
                    wrapper.pop_deadline()
                    local_flag = True

            if local_flag:
                self.deadline_flag = +self.deadline_flag
            time.sleep(1)

    def _answer_requests(self):
        while True:
            to_delete = dict()

            for product, count in self.requests_in_process.items():
                with self.thread_locker:
                    if self.requests_queue._queue and product in self.requests_queue._queue[0]:
                        to_send = min(count, self.requests_queue._queue[0][product])
                        to_delete[product] = to_send
                        self.requests_queue._queue[0] -= SelectionRequest((product, to_send))

            with self.thread_locker:
                for product, count in to_delete.items():
                    self.requests_in_process[product] -= count

            time.sleep(5)

    def _run_thread(self, sync_func) -> None:
        thread = threading.Thread(target=sync_func, daemon=True)
        self.__threads.append(thread)
        thread.start()

    async def check_flags_and_run(self):
        request = None

        if self.deadline_flag:
            with self.thread_locker:
                request = self.deadline_flag.request
                self.deadline_flag = -self.deadline_flag
        elif self.full_stack_flag:
            with self.thread_locker:
                request = self.full_stack_flag.request
                self.full_stack_flag = -self.full_stack_flag
        elif self.one_product_left_flag:
            with self.thread_locker:
                request = self.one_product_left_flag.request
                self.one_product_left_flag = -self.one_product_left_flag

        if request:
            await self.add_to_process(request)
            clusters = await self.choose_clusters(request)
            cells = await self.choose_cells(request, clusters)
            way = await self.build_way(cells)

            with self.thread_locker:
                async with self.async_locker:
                    self.outbox_container.append(way)

    async def add_to_process(self, request: SelectionRequest) -> None:
        with self.thread_locker:
            async with self.async_locker:
                for product, count in request.items():
                    self.requests_in_wait[product].count -= count
                    self.requests_in_process[product] = self.requests_in_process.get(product, 0) + count

    @run_async_thread(executor__)
    def choose_clusters(self, request: SelectionRequest) -> set[Cluster]:
        result = set()

        for product, count in request.items():
            for cluster in self.clusters_controller.get_clusters():
                if cluster.score_for_product(product.sku) > 2 * count:
                    result.add(cluster)

        return result

    @run_async_thread(executor__)
    def choose_cells(self, request: SelectionRequest, clusters: set[Cluster]) -> set[Cell]:
        settings = {
            'population_size': 100,
            'generations': 1000,
            'mutation_rate': 0.33
        }

        sup_cluster = {
            str(cell.cell_id): cell
            for cluster in clusters
            for cell in cluster.cells
        }

        order = {
            product.sku: count
            for product, count in request.items()
        }

        genetic_algorithm = GeneticAlgorithm(sup_cluster)
        return genetic_algorithm.evolution(order, settings)

    @run_async_thread(executor__)
    def build_way(self, cells: set[Cell]) -> list[int]:
        return adapter(self.warehouse, cells)
