from random import randint, random
from math import exp, hypot
from itertools import product

Point = tuple[float, float]
Path = list[Point]


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
        swap1 = swap2 = len(self.path) - 1
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


def adapter(warehouse, cells: set) -> list[tuple[int, int]]:
    dots = [(cell.x, cell.y) for cell in cells]
    dots.insert(0, warehouse.get_start())
    dots.append(warehouse.get_start())
    Otjig().optimise(dots, len(dots))

    available = set()
    for pos in product(*map(range, [warehouse.width(), warehouse.height()])):
        if warehouse.is_moving_cell(pos):
            available.add(pos)

    path = [dots[0]]
    prev = dots[0]
    for dot in dots[1:]:
        burned = set()
        dfs = [prev]

        while dfs[-1] != dot:
            burned.add(dfs[-1])
            cur_x, cur_y = dfs[-1]
            neighbors = [
                (cur_x + 1, cur_y),
                (cur_x - 1, cur_y),
                (cur_x, cur_y + 1),
                (cur_x, cur_y - 1),
            ]
            candidates = [
                pos for pos in neighbors
                if (pos in available and pos not in burned) or pos == dot
            ]
            if candidates:
                candidates.sort(
                    key=lambda pos: abs(pos[0] - dot[0]) + abs(pos[1] - dot[1])
                )
                dfs.append(candidates[0])
            else:
                dfs.pop()
        dfs.append(dfs[-2])
        path += dfs[1:]
        prev = path[-1]
    path.pop()
    return path