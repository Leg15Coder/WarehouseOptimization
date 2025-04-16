from src.algorithm.app import SizeType

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import LabelEncoder


class Clusterizer:
    class Cluster:
        def __init__(self, cluster_id: int, cell_ids: list[int]):
            self.id = cluster_id
            self.cell_ids = set(cell_ids)

        def __repr__(self):
            return f"<Cluster {self.id}: {len(self.cell_ids)} cells>"

        def contains(self, obj) -> bool:
            if isinstance(obj, int):
                return obj in self.cell_ids
            return False

    clusters: set[Cluster] = None
    warehouse: Warehouse = None
    parameters: dict = dict()
    size_type: SizeType = None

    __eps: float = 5
    __min_samples: int = 3

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    async def analyze(self) -> SizeType:
        """
        Анализирует масштаб склада и на основе этого подбирает подходящие параметры кластеризации.
        """

        # Получаем габариты склада
        width = self.warehouse.width
        height = self.warehouse.height
        num_cells = self.warehouse.total_cell_count  # Общее количество ячеек

        area = width * height
        density = num_cells / area if area else 0

        # Определяем размер склада по числу ячеек
        if num_cells < 40:
            self.size_type = SizeType.TINY
        elif num_cells < 500:
            self.size_type = SizeType.SMALL
        elif num_cells < 2000:
            self.size_type = SizeType.MEDIUM
        elif num_cells < 5000:
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

        async with db.connection() as conn:
            cells_df = await conn.fetch_df(query)    # conn возьму из Database class

        if cells_df.empty:
            return  # Сообщить об ошибке

        # Подсчёт заполненности
        cells_df['fill_ratio'] = cells_df['count'] / cells_df['max_amount']

        # Кодирование категориального признака
        le = LabelEncoder()
        cells_df['product_type_encoded'] = le.fit_transform(cells_df['product_type'])

        # Вектор признаков: X, Y, заполненность, тип
        features = cells_df[['x', 'y', 'fill_ratio', 'product_type_encoded']].values

        # Кластеризация
        clustering = DBSCAN(eps=self.__eps, min_samples=self.__min_samples).fit(features)
        cells_df['cluster'] = clustering.labels_

        self.clusters = {
            self.Cluster(cluster_id, group['cell_id'].tolist())
            for cluster_id, group in cells_df.groupby('cluster')
            if cluster_id != -1
        }

        self.noise = {
            self.Cluster(cluster_id, group['cell_id'].tolist())
            for cluster_id, group in cells_df.groupby('cluster')
            if cluster_id == -1  # -1 означает "шум" в DBSCAN
        }

    async def get_clusters(self) -> set[Clusters]:
        if self.clusters is None:
            await self.clusterize()

        return self.clusters
