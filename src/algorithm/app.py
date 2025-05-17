import asyncio
from asyncio import Queue
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


executor__ = ThreadPoolExecutor(max_workers=256)


class ProductWrapper:
    def __init__(self, product: Product, nearest_deadline: datetime):
        self.product = product
        self.nearest_deadline = nearest_deadline

    def __eq__(self, other):
        return (isinstance(other, Product) and other == self.product) or other.product == self.product

    def __hash__(self):
        return hash(self.product)


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

    requests_queue: Queue[SelectionRequest]
    requests_in_wait: dict[ProductWrapper, int]
    requests_in_process: dict[ProductWrapper, int]
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

        self.requests_queue = Queue()
        self.requests_in_wait = dict()
        self.requests_in_process = dict()
        self.outbox_container = list()

        self._stop_event = threading.Event()

    async def start(self):
        self._async_task = asyncio.create_task(self.check_flags())
        self.size_type = await self.clusters_controller.analyze()

    def __del__(self):
        self._stop_event.set()

        if hasattr(self, '_async_task'):
            self._async_task.cancel()

        executor__.shutdown(wait=False)

        for thread in self.__threads:
            if thread.is_alive():
                thread.join(timeout=1)

    async def solve(self, request: SelectionRequest) -> Optional[str]:
        with self.thread_locker:
            async with self.async_locker:
                await self.requests_queue.put(request)

                for product, count in request.items():
                    wrapper = ProductWrapper(product, datetime.now() + timedelta(seconds=10))
                    self.requests_in_wait[wrapper] = self.requests_in_wait.get(wrapper, 0) + count

                if bool(self.outbox_container):
                    self.outbox_container.clear()
                    return "SUCCESS"

    async def check_flags(self):
        self._run_thread(self._watch_flags_loop)
        self._run_thread(self._watch_one_product_left)
        self._run_thread(self._schedule_deadline_check)

        while True:
            await self.run_algorithm()
            await asyncio.sleep(0.1)

    def _watch_flags_loop(self):
        while True:
            local_flag = False
            for wrapper, count in self.requests_in_wait.items():
                if count >= wrapper.product.max_per_hand:
                    self.full_stack_flag |= SelectionRequest((wrapper.product, count))
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

            for wrapper, count in self.requests_in_wait.items():
                if wrapper.nearest_deadline - timedelta(seconds=5) <= datetime.now():
                    self.deadline_flag |= SelectionRequest((wrapper.product, count))
                    local_flag = True

            if local_flag:
                self.deadline_flag = +self.deadline_flag
            time.sleep(1)

    def _run_thread(self, sync_func) -> None:
        thread = threading.Thread(target=sync_func, daemon=True)
        self.__threads.append(thread)
        thread.start()

    async def run_algorithm(self):
        clusters, request = None, None
        if self.deadline_flag:
            with self.thread_locker:
                async with self.async_locker:
                    await self.add_to_process(self.deadline_flag.request)
                    request = self.deadline_flag.request
                    clusters = await self.choose_clusters(self.deadline_flag.request)

        elif self.full_stack_flag:
            with self.thread_locker:
                async with self.async_locker:
                    await self.add_to_process(self.full_stack_flag.request)
                    request = self.full_stack_flag.request
                    clusters = await self.choose_clusters(self.full_stack_flag.request)

        elif self.one_product_left_flag:
            with self.thread_locker:
                async with self.async_locker:
                    await self.add_to_process(self.one_product_left_flag.request)
                    request = self.one_product_left_flag.request
                    clusters = await self.choose_clusters(self.one_product_left_flag.request)

        if clusters:
            cells = await self.choose_cells(request, clusters)
            self.outbox_container.append(await self.build_way(cells))

    async def add_to_process(self, request: SelectionRequest) -> None:
        with self.thread_locker:
            async with self.async_locker:
                for product, count in request.items():
                    wrapper = ProductWrapper(product, None)
                    self.requests_in_wait[wrapper] -= count
                    self.requests_in_process[wrapper] += self.requests_in_process.get(wrapper, 0) + count

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
            'population_size': 300,
            'generations': 1600,
            'mutation_rate': 0.3
        }

        sup_cluster = {
            str(cell.cell_id): cell
            for cluster in clusters
            for cell in cluster.cells
        }

        order = {
            str(product): count
            for product, count in request.items()
        }

        genetic_algorithm = GeneticAlgorithm(sup_cluster)
        return genetic_algorithm.evolution(order, settings)

    @run_async_thread(executor__)
    def build_way(self, cells: set[Cell]) -> list[int]:
        return [cell.cell_id for cell in cells]
