from random import randint, random
from math import exp, hypot
from itertools import product
import heapq

from pydantic.tools import lru_cache

from src.models.warehouse_on_db import Warehouse

Point = tuple[float, float]
Path = list[Point]


@lru_cache(maxsize=100000)
def dist(p1: Point, p2: Point) -> float:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def length(path: Path) -> float:
    result = 0.0
    for i in range(len(path) - 1):
        result += dist(path[i], path[i + 1])
    return result


base_temp = 1.0


class Otjig:
    # Выбирает use точек (включая стартовую) минимизируя длину пути между ними
    def optimise(self, dots: list[Point], use: int, iterations=1000):
        self.path = dots
        self.use = use
        self.temp = base_temp
        self.length = length(self.path[:use])
        if len(self.path) < 4:
            return
        for _ in range(iterations):
            self.__iterate()

    def __elem_dist(self, id1: int, id2: int) -> float:
        return dist(self.path[id1], self.path[id2])

    # Расчет вероятности перехода исходя из новой длины пути
    def __escape_chance(self, new_len: float) -> float:
        delta = self.length - new_len
        # Если новый путь короче или равен старому, принимаем всегда
        if delta >= 0:
            return 1.0
        x = delta / self.temp
        # Ограничиваем слишком малые x, чтобы избежать переполнения
        if x < -100:
            return 0.0
        return exp(x)

    # Функция остывания
    def __cool(self):
        self.temp *= 0.99

    # Основная итерация оптимизатора
    def __iterate(self):
        swap1 = len(self.path) - 1
        swap2 = len(self.path) - 1
        while swap1 == len(self.path) - 1 or swap2 == len(self.path) - 1:
            swap1 = randint(1, self.use - 1)
            swap2 = randint(1, len(self.path) - 2)

            if swap1 == swap2:
                swap2 = 1 if (swap1 == len(self.path) - 1) else swap1 + 1
            if swap1 > swap2:
                swap1, swap2 = swap2, swap1

        new_len = self.length
        if swap2 < self.use:
            new_len += self.__elem_dist(swap1 - 1, swap2) - self.__elem_dist(swap1 - 1, swap1)
            new_len += self.__elem_dist(swap1 + 1, swap2) - self.__elem_dist(swap1 + 1, swap1)
            new_len += self.__elem_dist(swap2 - 1, swap1) - self.__elem_dist(swap2 - 1, swap2)
            if swap2 != self.use - 1:
                new_len += self.__elem_dist(swap2 + 1, swap1) - self.__elem_dist(swap2 + 1, swap2)
        else:
            new_len += self.__elem_dist(swap1 - 1, swap2) - self.__elem_dist(swap1 - 1, swap1)
            if swap1 != self.use - 1:
                new_len += self.__elem_dist(swap1 + 1, swap2) - self.__elem_dist(swap1 + 1, swap1)

        rnd_val = random()
        if rnd_val < self.__escape_chance(new_len):
            self.path[swap1], self.path[swap2] = self.path[swap2], self.path[swap1]
            self.length = new_len

        self.__cool()


def zip_way(way: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    result = list()
    result.append(way[0])
    cur_direction = (way[1][0] - way[0][0], way[1][1] - way[0][1])
    is_product = False
    for i in range(1, len(way)):
        path = way[i]
        direct = (path[0] - way[i - 1][0], path[1] - way[i - 1][1])
        if path[2] == 'product':
            is_product = True
            cur_direction = direct
            result.append(way[i - 1])
        elif is_product:
            is_product = False
            cur_direction = (0, 0)
            result.append(way[i - 1])
        elif direct != cur_direction:
            cur_direction = direct
            result.append(way[i - 1])
    result.append(way[-1])
    return result


def adapter(warehouse: Warehouse, cells: set) -> list[tuple[int, int]]:
    dots = [(cell.x, cell.y) for cell in cells]
    dots.insert(0, warehouse.get_start())
    dots.append(warehouse.get_start())
    Otjig().optimise(dots, len(dots))

    result = list()
    for i in range(len(dots) - 1):
        comes_from = dict()
        open_set = [(dist(dots[i], dots[i + 1]), 0, dots[i])]
        comes_from[dots[i]] = None
        visited = set()

        while open_set:
            est_total, path_len, current = heapq.heappop(open_set)
            if current == dots[i + 1]:
                to_extend = list()
                while current is not None:
                    to_extend.append(current)
                    current = comes_from[current]

                to_extend.pop()
                result.extend(reversed(to_extend))
                break
            if current in visited:
                continue
            visited.add(current)

            x, y = current
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbor = (x + dx, y + dy)
                if neighbor == dots[i + 1] or warehouse.is_moving_cell(neighbor):
                    if neighbor not in visited:
                        comes_from[neighbor] = current
                        heapq.heappush(open_set, (
                            path_len + 1 + dist(neighbor, dots[i + 1]),
                            path_len + 1,
                            neighbor
                        ))
        else:
            raise ValueError(f"Нет пути от {start} до {goal}")

    products = set(dots) - {warehouse.get_start()}
    result = [(x, y, "product" if (x, y) in products else "passage") for x, y in result]
    result = zip_way(result)
    return result
