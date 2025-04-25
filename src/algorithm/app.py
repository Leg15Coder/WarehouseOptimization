import asyncio
from asyncio import PriorityQueue
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from utils import run_async_thread
from clusterizer.Clusterizer.Cluster import Cell
from clusterizer import Clusterizer


class SizeType(Enum):
    TINY = 1
    SMALL = 2
    MEDIUM = 3
    LARGE = 4
    EXTRA_LARGE = 5


class Algorithm:
    class __FlagContainer:
        def __init__(self):
            self.flag = False
            self.request = SelectionRequest()

        def __ior__(self, other: SelectionRequest):
            self.requests |= other
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

    class ProductWrapper:
        def __init__(self, product: Product, nearest_deadline: datetime):
            self.product = product
            self.nearest_deadline = nearest_deadline

    warehouse: Warehouse
    clusters_controller: Clusterizer
    size_type: SizeType

    requests_queue: PriorityQueue[SelectionRequest]
    requests_in_wait: dict[Product, int]
    requests_in_process: dict[Product, int]
    outbox_container: list

    deadline_flag: __FlagContainer = __FlagContainer()
    full_stack_flag: __FlagContainer = __FlagContainer()
    one_product_left_flag: __FlagContainer = __FlagContainer()

    thread_locker: threading.Lock = threading.Lock()
    async_locker: asyncio.Lock = asyncio.Lock()
    _stop_event: threading.Event
    __threads: list[threading.Thread] = list()
    __executor: ThreadPoolExecutor
    _async_task: asyncio.Task

    def __init__(self):
        self.warehouse = Warehouse()
        self.clusters_controller = Clusterizer(self.warehouse)
        self.size_type = self.clusters_controller.analyze()

        self.requests_queue = PriorityQueue()
        self.requests_in_wait = dict()
        self.requests_in_process = dict()
        self.outbox_container = list()

        self._stop_event = threading.Event()
        self.__executor = ThreadPoolExecutor(max_workers=256)
        self._async_task = asyncio.create_task(self.check_flags())

    def __del__(self):
        self._stop_event.set()

        if hasattr(self, '_async_task'):
            self._async_task.cancel()

        self.__executor.shutdown(wait=False)

        for thread in self.__threads:
            if thread.is_alive():
                thread.join(timeout=1)

    async def solve(self, request: SelectionRequest) -> Optional[str]:
        async with self.thread_locker, self.async_locker:
            await self.requests_queue.put(request)

            for product in request:
                count = request[product]
                if product in self.requests_in_wait:
                    self.requests_in_wait[product] += count
                else:
                    self.requests_in_wait[product] = count

            if bool(self.outbox_container):
                self.outbox_container.clear()
                return "SUCCESS"

    async def check_flags(self):
        self._run_thread(self._watch_flags_loop)
        self._run_thread(self._watch_one_product_left)
        self._run_thread(self._schedule_deadline_check)

        while True:
            await asyncio.get_running_loop().run_in_executor(None, func)
            await asyncio.sleep(1)

    def _watch_flags_loop(self):
        while True:
            local_flag = False
            for wrapper, count in self.requests_in_wait.items():
                if count >= wrapper.product.max_per_hand:
                    self.full_stack_flag |= SelectionRequest(((product, count), ))
                    local_flag = True

            if local_flag:
                self.full_stack_flag = +self.full_stack_flag
            datatime.time.sleep(1)

    def _watch_one_product_left(self):
        while True:
            continue  # todo later
            local_flag = False
            for request in self.requests_queue:
                if abs(request) == 1:  # Остался последний товар
                    self.one_product_left_flag |= request
                    local_flag = True

            if local_flag:
                self.one_product_left_flag = +self.one_product_left_flag
            datatime.time.sleep(1)

    def _schedule_deadline_check(self):
        while True:
            local_flag = False

            for wrapper, count in self.requests_in_wait.items():
                if wrapper.nearest_deadline + timedelta(seconds=5) >= datetime.now():
                    self.deadline_flag |= SelectionRequest(((wrapper.product, count), ))
                    local_flag = True

            if local_flag:
                self.deadline_flag = +self.deadline_flag
            datatime.time.sleep(1)

    def _run_thread(self, sync_func) -> None:
        thread = threading.Thread(target=sync_func, daemon=True)
        self.__threads.append(thread)
        thread.start()

    async def run_algorithm(self):
        clusters = None
        if self.deadline_flag:
            async with self.thread_locker, self.async_locker:
                await self.add_to_process(self.deadline_flag.request)
                clusters = await self.choose_clusters(self.deadline_flag.request)

        elif self.full_stack_flag:
            async with self.thread_locker, self.async_locker:
                await self.add_to_process(self.full_stack_flag.request)
                clusters = await self.choose_clusters(self.full_stack_flag.request)

        elif self.one_product_left_flag:
            async with self.thread_locker, self.async_locker:
                await self.add_to_process(self.one_product_left_flag.request)
                clusters = await self.choose_clusters(self.one_product_left_flag.request)

        if clusters:
            cells = await self.choose_cells(clusters)
            self.outbox_container.append(await self.build_way(cells))

    async def add_to_process(self, request: SelectionRequest) -> None:
        async with self.thread_locker, self.async_locker:
            for product in request:
                count = request[product]
                self.requests_in_wait[ProductWrapper(product, None)] -= count
                self.requests_in_process[ProductWrapper(product, None)] += count

    @run_async_thread(self.__executor)
    def choose_clusters(self, request: SelectionRequest) -> set[Cluster]:
        result = set()

        for product in request:
            count = request[product]

            for cluster in self.clusters_controller.clusters:
                if cluster.score_for_product(product.sku) > 2 * count:
                    result.add(cluster)

        return result

    @run_async_thread(self.__executor)
    def choose_cells(self, clusters: set[Cluster]) -> set[Cell]:
        pass

    @run_async_thread(self.__executor)
    def build_way(self, cells: set[Cell]) -> list[int]:
        pass
