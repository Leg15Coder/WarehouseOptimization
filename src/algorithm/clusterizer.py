from src.algorithm.app import SizeType


class Clusterizer:
    class Cluster:
        pass

    clusters: set[Cluster]
    warehouse: Warehouse
    parameters: dict
    size_type: SizeType

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    def analyze(self) -> SizeType:
        pass

    def clusterize(self):
        pass

    def get_clusters(self) -> set[Clusters]:
        pass
