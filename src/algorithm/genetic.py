import random
from math import sqrt
from collections import defaultdict

class GeneticAlgorithm:
    GENERATIONS = 100
    MIN_MUTATION_RATE = 0.3
    ELITISM_RATE = 0.1
    PERFECT_FITNESS = 0.3

    def __init__(self, warehouse: dict):
        self.query = None
        self.warehouse = warehouse
        self.POPULATION_SIZE = len(warehouse)

    def distance(self, cell1, cell2):
        """Расчет расстояния между двумя ячейками"""
        x1, y1 = self.warehouse[cell1]['coords']
        x2, y2 = self.warehouse[cell2]['coords']
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


    def total_distance(self, selection):
        """Общее расстояние между выбранными ячейками (уникальными)"""
        unique_cells = list(set(selection))
        if len(unique_cells) < 2:
            return 0
        return sum(self.distance(unique_cells[i], unique_cells[i + 1])
                   for i in range(len(unique_cells) - 1))


    def meets_request(self, selection):
        """Проверяет, удовлетворяет ли выборка запросу (без дубликатов ячеек)"""
        collected = defaultdict(int)
        unique_cells = set(selection)  # Убираем дубликаты

        for cell in unique_cells:
            item = self.warehouse[cell]['type']
            collected[item] += self.warehouse[cell]['qty']

        for item, needed in self.query.items():
            if collected[item] < needed:
                return False
        return True


    def fitness(self, selection):
        unique_cells = list(set(selection))

        if not self.meets_request(unique_cells):
            return 0

        dist = self.total_distance(unique_cells)
        return 1 / dist


    def create_individual(self):
        individual = []
        collected = defaultdict(int)
        available_cells = list(self.warehouse.keys())
        random.shuffle(available_cells)

        for cell in available_cells:
            item = self.warehouse[cell]['type']
            if collected[item] < self.query.get(item, 0):
                individual.append(cell)
                collected[item] += self.warehouse[cell]['qty']
        return individual


    def mutaterate(self, individual):
        return 1 - self.fitness(individual) * 10


    def mutate(self, individual):
        if random.random() < self.mutaterate(individual):
            mutation_type = random.choice(['replace', 'add', 'remove'])
            unique_cells = set(individual)
            available_cells = [c for c in self.warehouse if c not in unique_cells]

            if mutation_type == 'replace' and individual and available_cells:
                idx = random.randint(0, len(individual) - 1)
                new_cell = random.choice(available_cells)
                individual[idx] = new_cell

            elif mutation_type == 'add' and available_cells:
                new_cell = random.choice(available_cells)
                individual.append(new_cell)

            elif mutation_type == 'remove' and len(individual) > 1:
                individual.pop(random.randint(0, len(individual) - 1))

        return individual


    def crossover(self, parent1, parent2):
        place = 0
        if random.randint(0, 10) < 7:
            place = random.randint(0, min(len(parent1), len(parent2)))
        else:
            return parent1, parent2
        return parent1, parent2, parent1[:place] + parent2[place:], parent2[:place] + parent1[place:]

    def genetic_algorithm(self):
        """Основной алгоритм с защитой от дубликатов"""
        best = self.create_individual()
        for generation in range(self.GENERATIONS):
            # Оценка приспособленности
            population = sorted([self.mutate(best) for _ in range(self.POPULATION_SIZE)], key=self.fitness, reverse=True)
            parent1 = population[0]
            parent2 = population[1]
            best = max(self.crossover(parent1, parent2), key=self.fitness)
        return best

    def solve(self, query, GENERATIONS=100):
        self.query = query
        self.GENERATIONS = GENERATIONS
        best_selection = self.genetic_algorithm()
        print("Лучший отбор ячеек:", best_selection)
        print("Фитнес:", self.fitness(best_selection))
        print("Общее расстояние:", self.total_distance(best_selection))

        # Проверяем удовлетворение запроса
        collected = defaultdict(int)
        for cell in best_selection:
            item = self.warehouse[cell]['type']
            collected[item] += self.warehouse[cell]['qty']
        print("Собранные товары:", dict(collected))


import random
import math
from collections import defaultdict

class GeneticAlgorithm:

    def __init__(self, warehouse):
        self.all_cells_data = warehouse
        self.MUTATION_RATE = None
        self.GENERATIONS = None
        self.POPULATION_SIZE = None

    def calculate_distance(self, coord1, coord2):
        # Евклидово расстояние (пример для 2D)
        return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

    def generate_valid_solution(self, current_order, locations, cells_data):
        """Генерирует ОДНО валидное решение (набор ID ячеек)."""
        selected_cell_ids = set()
        # Важно: создаем копию доступности, чтобы не портить глобальные данные
        temp_availability = {cid: data["quantity"] for cid, data in cells_data.items()}

        order_items = list(current_order.items())
        random.shuffle(order_items)  # Случайный порядок обхода товаров

        for item_type, required_qty in order_items:
            possible_cell_ids = list(locations.get(item_type, []))
            random.shuffle(possible_cell_ids)  # Случайный порядок обхода ячеек

            qty_needed = required_qty

            # Эвристика: сначала попробуем ячейки, которые УЖЕ выбраны для других товаров
            preferred_cells = [cid for cid in possible_cell_ids if cid in selected_cell_ids]
            other_cells = [cid for cid in possible_cell_ids if cid not in selected_cell_ids]

            # Объединяем, предпочитая уже выбранные
            ordered_cells_to_check = preferred_cells + other_cells

            for cell_id in ordered_cells_to_check:
                if qty_needed <= 0:
                    break

                available_in_cell = temp_availability.get(cell_id, 0)

                if available_in_cell > 0:
                    pick_qty = min(qty_needed, available_in_cell)
                    selected_cell_ids.add(cell_id)
                    temp_availability[cell_id] -= pick_qty  # Уменьшаем доступность *временно*
                    qty_needed -= pick_qty

            if qty_needed > 0:
                # Если не хватило товара - ошибка в данных или логике
                raise ValueError(f"Невозможно выполнить заказ: не хватает товара {item_type}")
                # В реальной системе здесь может быть логика обработки нехватки

        return list(selected_cell_ids)  # Возвращаем список уникальных ID


    def calculate_fitness(self, solution_cell_ids, cells_data):
        """Вычисляет пригодность решения (чем меньше значение, тем лучше)."""
        if not solution_cell_ids:
            return float('inf')  # Худшее значение для пустого решения

        coords = [cells_data[cid]['coords'] for cid in solution_cell_ids]

        # Вариант 1: Сумма попарных расстояний
        total_dist = 0
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                total_dist += self.calculate_distance(coords[i], coords[j])

        # Вариант 2: Среднее расстояние до центроида (пример)
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        centroid = (cx, cy)
        total_dist = sum(self.calculate_distance(c, centroid) for c in coords)
        avg_dist = total_dist / len(coords) if coords else 0
        num_cells_penalty = len(solution_cell_ids) * 0.1

        return total_dist + num_cells_penalty + avg_dist


    def mutate_solution(self, parent_solution_ids, current_order, locations, cells_data):
        """
        Мутирует решение, пытаясь заменить выбор ячеек для одного из товаров.
        Возвращает новое валидное решение.
        """
        if not parent_solution_ids or random.random() > self.MUTATION_RATE:  # Вероятность мутации
            return parent_solution_ids[:]

        mutated_solution_ids = list(parent_solution_ids)

        # Выбираем случайный товар из заказа, который представлен в решении
        items_in_solution = defaultdict(list)
        for cid in mutated_solution_ids:
            item = cells_data[cid]["type"]
            if item in current_order:
                items_in_solution[item].append(cid)

        possible_items_to_mutate = list(items_in_solution.keys())
        if not possible_items_to_mutate:
            return mutated_solution_ids

        item_to_remutate = random.choice(possible_items_to_mutate)

        # Ячейки, НЕ связанные с этим товаром (приблизительно, т.к. ячейка может иметь >1 товара, но здесь модель проще)
        other_cells = set(cid for cid in mutated_solution_ids if cells_data[cid]['type'] != item_to_remutate)

        # Создаем временный заказ только для этого товара
        temp_order = {item_to_remutate: current_order[item_to_remutate]}

        # Генерируем новый набор ячеек ТОЛЬКО для этого товара
        # Передаем 'other_cells' как потенциально предпочитаемые
        try:
            # Нужна функция, которая сможет переиспользовать 'other_cells' и добавлять новые
            # Упрощенный вариант: генерируем заново и объединяем
            new_cells_for_item = self.generate_valid_solution(temp_order, locations, cells_data)
            # В идеале, generate_valid_solution должна уметь учитывать уже выбранные 'other_cells'
            # и стараться переиспользовать их или выбирать ячейки рядом с ними.

            # Объединяем старые ячейки (для других товаров) и новые (для мутируемого товара)
            final_mutated_ids = list(other_cells.union(set(new_cells_for_item)))
            return final_mutated_ids

        except ValueError:
            # Если не удалось сгенерировать замену (маловероятно, но возможно)
            return mutated_solution_ids  # Возвращаем оригинал

    def evolution(self, order, settings):
        self.POPULATION_SIZE = settings['population_size']
        self.GENERATIONS = settings['generations'] # Количество поколений (или другое условие останова)
        self.MUTATION_RATE = settings['mutation_rate'] # Вероятность, что особь будет мутировать (надо подогнать)

        item_locations = {}
        for cell_id, cell_data in self.all_cells_data.items():
            if cell_data['type'] not in item_locations:
                item_locations[cell_data['type']] = []
            item_locations[cell_data['type']].append(cell_id)

        population = [self.generate_valid_solution(order, item_locations, self.all_cells_data) for _ in range(self.POPULATION_SIZE)]
        fitness_values = [self.calculate_fitness(ind, self.all_cells_data) for ind in population]

        best_solution = None
        best_fitness = float('inf')

        for generation in range(self.GENERATIONS):
            current_best_idx = min(range(self.POPULATION_SIZE), key=lambda fitness: fitness_values[fitness])
            if fitness_values[current_best_idx] < best_fitness:
                best_fitness = fitness_values[current_best_idx]
                best_solution = population[current_best_idx][:]
                print(
                    f"Generation {generation}: New best fitness = {best_fitness:.2f}, Cells = {len(best_solution)}")  # , Solution = {best_solution}")

            # 2. Генерация нового поколения (простой вариант: мутируем всех и выбираем лучших)
            new_population = []
            new_fitness_values = []

            # Элитарность: сохраняем лучшего из предыдущего поколения
            new_population.append(best_solution)
            new_fitness_values.append(best_fitness)

            # Генерируем остальных мутациями (можно мутировать лучших, или всех)
            for i in range(self.POPULATION_SIZE - 1):
                # Выбираем родителя (например, лучшего или случайного из лучших N)
                parent_idx = current_best_idx  # Простая стратегия: мутируем лучшего
                # parent_idx = random.choices(range(self.POPULATION_SIZE), weights=[1/(f+1e-9) for f in fitness_values], k=1)[0]

                mutant = self.mutate_solution(population[parent_idx], order, item_locations, self.all_cells_data)
                mutant_fitness = self.calculate_fitness(mutant, self.all_cells_data)

                new_population.append(mutant)
                new_fitness_values.append(mutant_fitness)

            population = new_population
            fitness_values = new_fitness_values
        print("\nFinished!")
        print(f"Request: {order}")
        print(f"Best solution fitness: {best_fitness:.2f}")
        print(f"Number of cells: {len(best_solution)}")
        print(f"Selected cell IDs: {best_solution}")


# Пример случайной генерации склада и запуска алгоритма
# Есть возможность запускать один и тот же набор данных с разным количестов поколений, размером популяции и т.д.
warehouse = {}
goods = ['apple', 'banana', 'orange', 'milk', 'bread']

for row in range(1, 6):
    for column in range(1, 6):
        cell_id = f"{row}-{column}"
        warehouse[cell_id] = {
            'id' : str(5 * (row - 1) + column),
            'coords': (row, column),
            'type': random.choice(goods),
            'quantity': random.randint(1, 10)
        }

for row in range(0, 5):
    for column in range(0, 5):
        current = list(warehouse.values())[5 * row + column]
        print(str(current['coords'][0]) + "-" + str(current['coords'][1]) + ";" + current['type'] + ";" + str(current['quantity']), end=" | ")
    print()

order = {
    'apple': 12,
    'banana': 8,
    'orange': 10,
    'milk': 5,
    'bread': 7
}

settings = {
    'population_size' : 100,
    'generations' : 500,
    'mutation_rate' : .3
}

alg = GeneticAlgorithm(warehouse)
alg.evolution(order, settings)
