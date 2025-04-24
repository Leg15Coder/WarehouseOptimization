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

    deadline_flag: __FlagContainer = __FlagContainer()
    full_stack_flag: __FlagContainer = __FlagContainer()
    one_product_left_flag: __FlagContainer = __FlagContainer()

    locker: threading.Lock = threading.Lock()

    def __init__(self):
        self.warehouse = Warehouse()
        self.clusters_controller = Clusterizer(self.warehouse)
        self.size_type = self.clusters_controller.analyze()

        self.requests_queue = PriorityQueue()
        self.requests_in_wait = dict()
        self.requests_in_process = dict()

        threading.Thread(target=self.check_flags, daemon=True).start()

    def check_flags(self):
        threading.Thread(target=self._watch_flags_loop, daemon=True).start()
        threading.Thread(target=self._watch_one_product_left, daemon=True).start()
        threading.Thread(target=self._schedule_deadline_check, daemon=True).start()

        while True:
            self.run_algorithm()
            asyncio.sleep(1)

    def _watch_flags_loop(self):
        while True:
            local_flag = False
            for wrapper, count in self.requests_in_wait.items():
                if count >= wrapper.product.max_per_hand:
                    self.full_stack_flag |= SelectionRequest(((product, count), ))
                    local_flag = True

            if local_flag:
                self.full_stack_flag = +self.full_stack_flag
            asyncio.sleep(1)

    def _watch_one_product_left(self):
        while True:
            continue
            local_flag = False
            for request in self.requests_queue:
                if abs(request) == 1:  # Остался последний товар
                    self.one_product_left_flag |= request
                    local_flag = True

            if local_flag:
                self.one_product_left_flag = +self.one_product_left_flag
            asyncio.sleep(1)

    def _schedule_deadline_check(self):
        while True:
            local_flag = False

            for wrapper, count in self.requests_in_wait.items():
                if wrapper.nearest_deadline + timedelta(seconds=5) >= datetime.now():
                    self.deadline_flag |= SelectionRequest(((wrapper.product, count), ))
                    local_flag = True

            if local_flag:
                self.deadline_flag = +self.deadline_flag
            asyncio.sleep(1)

    async def run_algorithm(self):
        clusters = None
        if self.deadline_flag:
            with self.locker:
                await self.add_to_process(self.deadline_flag.request)
                clusters = await self.choose_clusters(self.deadline_flag.request)

        elif self.full_stack_flag:
            with self.locker:
                await self.add_to_process(self.full_stack_flag.request)
                clusters = await self.choose_clusters(self.full_stack_flag.request)

        elif self.one_product_left_flag:
            with self.locker:
                await self.add_to_process(self.one_product_left_flag.request)
                clusters = await self.choose_clusters(self.one_product_left_flag.request)

        if clusters:
            cells = self.choose_cells(clusters)
            path = self.build_way(cells)
            return path

    async def add_to_process(self, request: SelectionRequest) -> None:
        with self.locker:
            for product in request:
                count = request[product]
                self.requests_in_wait[ProductWrapper(product, None)] -= count
                self.requests_in_process[ProductWrapper(product, None)] += count

    async def solve(self, request: SelectionRequest) -> Optional[str]:
        pass

    async def choose_clusters(self, request: SelectionRequest) -> list[Cluster]:
        pass

    async def choose_cells(self, clusters: list[Cluster]) -> set[int]:
        pass

    async def build_way(self, cells: set[int]) -> list[int]:
        pass
