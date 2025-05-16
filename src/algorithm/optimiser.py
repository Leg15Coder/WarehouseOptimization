from random import randint, random
from math import exp, hypot

Point = tuple[float, float]
Path = list[Point]

def dist(p1: Point, p2: Point) -> float:
    return hypot(p1[0] - p2[0], p1[1] - p2[1])

def lenght(path: Path) -> float:
    result = 0.0
    for i in range(len(path) - 1):
        result += dist(path[i], path[i + 1])
    return result

base_temp = 1.0

class Otjig:
    # Выбирает use точек (включая стартовую) минимузируя длину пути между ними
    def optimise(self, dots: list[Point], use: int, iterations=1000):
        self.path = dots
        self.use = use
        self.temp = base_temp
        self.length = lenght(self.path[:use])
        for i in range(iterations):
            self.__iterate()
    
    def __elem_dist(self, id1: int, id2: int) -> float:
        return dist(self.path[id1], self.path[id2])
    
    # Расчет вероятности перехода исходя из новой длины пути
    def __escape_chance(self, new_len: float) -> float:
        return exp((self.length - new_len) / self.temp)
    
    # Функция остывания
    def __cool(self):
        self.temp *= 0.99

    # функция оптимизатор
    def __iterate(self):
        # Выбор элементов для свапа
        swap1 = randint(1, self.use - 1)
        swap2 = randint(1, len(self.cur) - 1)
        
        # Корректировка выбора
        if swap1 == swap2:
            swap2 = 1 if (swap1 == len(self.path) - 1) else swap1 + 1
        if swap1 > swap2:
            swap1, swap2 = swap2, swap1
        
        # Расчет новой длины
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

        # Принятие решения о применении изменения
        rnd_val = random()
        if rnd_val < self.__escape_chance(new_len):
            self.path[swap1], self.path[swap2] = self.path[swap2], self.path[swap1]
            self.length = new_len
        self.__cool()


def adapter(self, cells : set) -> list[int]:
    dots = [(cell.x, cell.y) for cell in cells]
    Otjig().optimise(dots, len(dots))
    ids = [cells[dots.find((cell.x, cell.y))].cell_id for cell in cells]
    return ids
