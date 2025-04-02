from enum import Enum


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

    requests_queue: list[SelectionRequest]
    products_stack: dict[Product, int]

    def __init__(self):
        self.warehouse = Warehouse()
        self.clusters_controller = Clusterizer(self.warehouse)
        self.size_type = self.clusters_controller.analyze()

    async def solve(self, request: SelectionRequest) -> Optional[str]:
        pass

    async def check_flags(self) -> bool:
        pass

    async def choose_clusters(self) -> list[Cluster]:
        pass

    async def choose_cells(self, clusters: list[Cluster]) -> set[int]:
        pass

    async def build_way(self, cells: set[int]) -> list[int]:
        pass
