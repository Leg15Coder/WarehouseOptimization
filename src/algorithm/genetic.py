import random
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Any, Optional


class GeneticAlgorithm:
    def __init__(self, warehouse: Dict[str, Cell]) -> None:
        self.all_cells_data: Dict[str, Cell] = warehouse
        self.MUTATION_RATE: Optional[float] = None
        self.GENERATIONS: Optional[int] = None
        self.POPULATION_SIZE: Optional[int] = None

    def calculate_distance(
        self, coord1: Tuple[float, float], coord2: Tuple[float, float]
    ) -> float:
        """Вычисляет евклидово расстояние между двумя точками."""
        return math.hypot(coord1[0] - coord2[0], coord1[1] - coord2[1])

    def generate_valid_solution(
        self,
        current_order: Dict[str, int],
        locations: Dict[str, List[str]],
    ) -> List[str]:
        """Генерирует один валидный набор ID ячеек."""
        selected: Set[str] = set()
        # Копируем доступность, чтобы не менять оригинальную
        temp_avail: Dict[str, int] = {
            cid: cell.count for cid, cell in self.all_cells_data.items()
        }

        items = list(current_order.items())
        random.shuffle(items)

        for product, qty_needed in items:
            possible = locations.get(product, [])[:]
            random.shuffle(possible)

            # Сначала ячейки, уже в selected
            preferred = [cid for cid in possible if cid in selected]
            others = [cid for cid in possible if cid not in selected]
            for cid in preferred + others:
                if qty_needed <= 0:
                    break
                avail = temp_avail.get(cid, 0)
                if avail <= 0:
                    continue
                take = min(qty_needed, avail)
                selected.add(cid)
                temp_avail[cid] -= take
                qty_needed -= take

            if qty_needed > 0:
                raise ValueError(f"Невозможно выполнить заказ: не хватает товара {product}")

        return list(selected)

    def calculate_fitness(
        self, solution_ids: List[str]
    ) -> float:
        """Подсчет пригодности: меньше — лучше."""
        if not solution_ids:
            return float('inf')

        coords = [(self.all_cells_data[cid].x, self.all_cells_data[cid].y)
                  for cid in solution_ids]
        # Сумма расстояний до центроида
        cx = sum(x for x, _ in coords) / len(coords)
        cy = sum(y for _, y in coords) / len(coords)
        centroid = (cx, cy)

        total = sum(
            self.calculate_distance(pt, centroid) for pt in coords
        )
        avg = total / len(coords)
        penalty = len(solution_ids) * 0.1
        return total + avg + penalty

    def mutate_solution(
        self,
        parent_ids: List[str],
        current_order: Dict[str, int],
        locations: Dict[str, List[str]],
    ) -> List[str]:
        """Мутация решения: заменяем ячейки одного товара."""
        if not parent_ids or random.random() > self.MUTATION_RATE:
            return parent_ids[:]

        # Группируем ячейки по продукту
        by_product: Dict[str, List[str]] = defaultdict(list)
        for cid in parent_ids:
            prod = self.all_cells_data[cid].product
            if prod in current_order:
                by_product[prod].append(cid)

        if not by_product:
            return parent_ids[:]

        product = random.choice(list(by_product.keys()))
        others = [cid for cid in parent_ids if self.all_cells_data[cid].product != product]

        temp_order = {product: current_order[product]}
        try:
            new_ids = self.generate_valid_solution(temp_order, locations)
            return others + new_ids
        except ValueError:
            return parent_ids[:]

    def evolution(
        self,
        order: Dict[str, int],
        settings: Dict[str, Any]
    ) -> None:
        """Запуск генетического алгоритма."""
        self.POPULATION_SIZE = settings['population_size']
        self.GENERATIONS = settings['generations']
        self.MUTATION_RATE = settings['mutation_rate']

        # Собираем список ячеек по продуктам
        locations: Dict[str, List[str]] = defaultdict(list)
        for cid, cell in self.all_cells_data.items():
            locations[cell.product].append(cid)

        # Инициализация популяции
        population = [
            self.generate_valid_solution(order, locations)
            for _ in range(self.POPULATION_SIZE)
        ]
        fitness = [self.calculate_fitness(sol) for sol in population]

        best_sol: Optional[List[str]] = None
        best_fit = float('inf')

        for gen in range(self.GENERATIONS):
            idx = min(range(len(population)), key=lambda i: fitness[i])
            if fitness[idx] < best_fit:
                best_fit = fitness[idx]
                best_sol = population[idx][:]
                # print(f"Generation {gen}: new best = {best_fit:.2f}, cells = {len(best_sol)}")

            new_pop = [best_sol]
            new_fit = [best_fit]
            for _ in range(self.POPULATION_SIZE - 1):
                child = self.mutate_solution(best_sol, order, locations)
                f = self.calculate_fitness(child)
                new_pop.append(child)
                new_fit.append(f)

            population, fitness = new_pop, new_fit

        return best_sol