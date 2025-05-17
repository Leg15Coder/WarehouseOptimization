import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import LabelEncoder

from src.algorithm.size_enum import SizeType
from src.models.cell import Cell
from src.models.warehouse_on_db import Warehouse
from src.models.product import Product
from src.parsers.db_parser import db


class Clusterizer:
    class Cluster:
        def __init__(self, warehouse: Warehouse, cluster_id: int, cell_ids: list[int]):
            self.id = cluster_id
            self.cells = {warehouse.get_cell_by_id(cell_id) for cell_id in cell_ids}
            self._product_counts = {}
            self._fill_ratios = {}
            self._centroid = None
            self._cache_data(self.cells)

        def __repr__(self):
            return f"<Cluster {self.id}: {len(self.cells)} cells>"

        def _cache_data(self, cells: set[Cell]):
            product_count = {}
            fill_ratio = {}

            total_x, total_y = 0, 0

            for cell in cells:
                product_count[cell.product.sku] = product_count.get(cell.product.sku, 0) + cell.count
                fill_ratio[cell.product.sku] = fill_ratio.get(cell.product.sku, 0) + cell.count / cell.product.max_amount
                total_x += cell.x
                total_y += cell.y

            self._product_counts = product_count
            self._fill_ratios = fill_ratio
            self._centroid = (total_x / len(cells), total_y / len(cells))

        def contains(self, obj) -> bool:
            if isinstance(obj, int):
                return obj in (cell.id for cell in self.cells)
            elif isinstance(obj, tuple):
                return obj in ((cell.x, cell.y) for cell in self.cells)
            elif isinstance(obj, Product):
                return obj in (cell.product for cell in self.cells)
            return False

        def score_for_product(self, product_sku: Product) -> float:
            count = self._product_counts.get(product_sku, 0)
            fill = self._fill_ratios.get(product_sku, 0)
            return count + fill

        def distance_to_point(self, point: tuple) -> float:
            return np.linalg.norm(np.array(self._centroid) - np.array(point))

    clusters: set[Cluster] = None
    warehouse: Warehouse = None
    parameters: dict = dict()
    size_type: SizeType = None

    __is_updated: bool = False
    __eps: float = 5
    __min_samples: int = 3

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    async def analyze(self) -> SizeType:
        """
        Анализирует масштаб склада и на основе этого подбирает подходящие параметры кластеризации.
        """

        # Получаем габариты склада
        width = self.warehouse.width()
        height = self.warehouse.height()
        num_cells = len(self.warehouse.get_all_cells())  # Общее количество ячеек

        area = width * height
        density = num_cells / area if area else 0

        # Определяем размер склада по числу ячеек
        if num_cells < 50:
            self.size_type = SizeType.TINY
        elif num_cells < 2000:
            self.size_type = SizeType.SMALL
        elif num_cells < 7000:
            self.size_type = SizeType.MEDIUM
        elif num_cells < 10000:
            self.size_type = SizeType.LARGE
        else:
            self.size_type = SizeType.EXTRA_LARGE

        # Настройка параметров DBSCAN по масштабу и плотности
        if self.size_type == SizeType.TINY:
            self.__eps = 2
            self.__min_samples = 2
        elif self.size_type == SizeType.SMALL:
            self.__eps = 3
            self.__min_samples = 3
        elif self.size_type == SizeType.MEDIUM:
            self.__eps = 5
            self.__min_samples = 4
        elif self.size_type == SizeType.LARGE:
            self.__eps = 7
            self.__min_samples = 5
        elif self.size_type == SizeType.EXTRA_LARGE:
            self.__eps = 10
            self.__min_samples = 6

        # Можно подкорректировать eps в зависимости от плотности (если надо):
        if density > 0.5:
            self.__eps *= 0.8  # плотный склад => ближе друг к другу
        elif density < 0.2:
            self.__eps *= 1.2  # разреженный склад

        self.__eps = round(self.__eps, 2)

        await self.clusterize()
        return self.size_type

    async def clusterize(self):
        query = """
                SELECT 
                    c.cell_id, c.x, c.y, 
                    c.count, 
                    p.max_amount, 
                    p.product_type
                FROM cell c
                JOIN product p ON c.product_sku = p.sku
                WHERE c.count > 0
            """

        with db.engine.connect() as conn:
            cells_df = pd.read_sql(query, conn)    # conn возьму из Database class

        if cells_df.empty:
            return  # Сообщить об ошибке

        # Подсчёт заполненности
        cells_df['fill_ratio'] = cells_df['count'] / cells_df['max_amount'] * 100

        # Кодирование категориального признака
        le = LabelEncoder()
        cells_df['product_type_encoded'] = le.fit_transform(cells_df['product_type'])

        start_x, start_y = self.warehouse.get_start()
        cells_df['dist_to_start'] = np.sqrt((cells_df['x'] - start_x) ** 2 + (cells_df['y'] - start_y) ** 2)

        features = cells_df[['x', 'y', 'fill_ratio', 'product_type_encoded', 'dist_to_start']].values

        # Кластеризация
        clustering = DBSCAN(eps=self.__eps, min_samples=self.__min_samples).fit(features)
        cells_df['cluster'] = clustering.labels_

        self.clusters = {
            self.Cluster(self.warehouse, cluster_id, group['cell_id'].tolist())
            for cluster_id, group in cells_df.groupby('cluster')
            if cluster_id != -1
        }

        self.clusters |= {
            self.Cluster(self.warehouse, cluster_id, group['cell_id'].tolist())
            for cluster_id, group in cells_df.groupby('cluster')
            if cluster_id == -1  # -1 означает "шум" в DBSCAN
        }

    async def get_clusters(self) -> set[Cluster]:
        if self.clusters is None or not self.__is_updated:
            await self.clusterize()
            self.__is_updated = True
            return self.clusters

        self.__is_updated = False
        return self.clusters


Cluster = Clusterizer.Cluster
