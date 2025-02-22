from random import randint, random
from math import exp, log

import numpy as np


class Warehouse():

    def __init__(self,
                 perpendicular_conveyor_x_coord=40,  # между 38 и 42, расположим по середине
                 perpendicular_conveyor_min_y_end=237,  # конвейер заканчивается и можно пройти "сквозь" него
                 perpendicular_conveyor_transition=87,  # зона "бригадира" -- 77 - 88, на 87 переход через конвейер
                 parallel_conveyor_y_coord=180,  # между 177 и 184, расположим по середине
                 parallel_conveyor_x_start=40,  # выходит из перпендикулярного конвейера
                 parallel_conveyor_x_end=0,  # конец конвейера слева (видимо уходит на этаж ниже), не везде есть
                 totes_buffs_coords=[[1.25, 4.5], [1.25, 88.5], [1.25, 176.5], [1.25, 212.5], [1.25, 240.5],
                                     [1.25, 268.5],
                                     [43.25, 4.5], [43.25, 88.5], [43.25, 176.5], [43.25, 212.5], [43.25, 240.5],
                                     [43.25, 268.5],
                                     [74.75, 4.5], [74.75, 88.5], [74.75, 176.5], [74.75, 212.5], [74.75, 240.5],
                                     [74.75, 268.5]
                                     ],  # координаты всех буфферов с тотами
                 no_transit_parallel_conv=[2],  # этаж, в которых нет перехода через параллельный конвейер
                 have_no_end_perpendicular_conveyor=[1],
                 passages_diff=3,
                 central_transition_left=17,
                 central_transition_right=60,
                 right_transition_x=77,
                 left_part_x_max=38,
                 right_part_x_min=42,
                 foreman_zone_y_start=77,
                 foreman_zone_y_end=88,
                 ladder_x_min=1,
                 ladder_x_max=3,
                 ladder_y_min=79,
                 ladder_y_max=80,
                 x_min=0,
                 x_max=78,
                 y_min=0,
                 y_max=272,
                 x_scale=1.02,  # перевод из х координат в метры
                 y_scale=0.55,  # перевод из y координат в метры
                 length_of_stairs=5  # длина лестницы в метрах
                 ):
        # определяем местоположение и переходы в конвейере, перпендикулярном стелажам
        self.perpendicular_conveyor_x_coord = perpendicular_conveyor_x_coord
        self.perpendicular_conveyor_min_y_end = perpendicular_conveyor_min_y_end
        self.perpendicular_conveyor_transition = perpendicular_conveyor_transition
        # определяем местоположение и переходы в конвейере, параллельного стелажам
        self.parallel_conveyor_y_coord = parallel_conveyor_y_coord
        self.parallel_conveyor_x_start = parallel_conveyor_x_start
        self.parallel_conveyor_x_end = parallel_conveyor_x_end

        self.totes_buffs_coords = totes_buffs_coords  # координаты буфферов с тотами

        self.no_transit_parallel_conv = no_transit_parallel_conv  # где, отсутствует проход через параллельный конвейер
        self.have_no_end_perpendicular_conveyor = have_no_end_perpendicular_conveyor  # где, отсутствует конец конвейера

        # координаты проходов в середине стелажей
        self.central_transition_left = central_transition_left
        self.central_transition_right = central_transition_right
        self.right_transition_x = right_transition_x
        self.left_part_x_max = left_part_x_max
        self.right_part_x_min = right_part_x_min

        self.passage_diff = passages_diff  # разница между y координатами, которая определяет проход

        # топология зоны с лестницей
        self.foreman_zone_y_start = foreman_zone_y_start
        self.foreman_zone_y_end = foreman_zone_y_end

        # лестница
        self.ladder_x_min = ladder_x_min
        self.ladder_x_max = ladder_x_max
        self.ladder_y_min = ladder_y_min
        self.ladder_y_max = ladder_y_max

        # ограничения этажа
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        # перевод из координат в метры
        self.x_scale = x_scale
        self.y_scale = y_scale

        # лестница
        self.length_of_stairs = length_of_stairs

    def get_foreman_zone_x_start(self):
        return 1

    def get_foreman_zone_x_end(self):
        return self.left_part_x_max

    def get_foreman_zone_y_start(self):
        return self.foreman_zone_y_start

    def get_foreman_zone_y_end(self):
        return self.foreman_zone_y_end

    def coordinates_check(self, x_1, y_1, x_2, y_2):

        if x_1 < self.x_min or x_2 < self.x_min or x_1 > self.x_max or x_2 > self.x_max \
                or y_1 < self.y_min or y_2 < self.y_min or y_1 > self.y_max or y_2 > self.y_max:
            return False  # если введены неправильные координаты, то вернуть ошибку
        return True  # введены правильные координаты

    def y_coordinate_normalization(self, y):
        if y > 272:
            return 272 - (y - 273)

        return y

    def get_totes_buffs_coords(self):
        return self.totes_buffs_coords

    def types_of_coordinates_on_the_same_floor(self, x_1, y_1, x_2, y_2):

        # сортируем координаты, чтобы первая точка имели координату по х не больше, чем вторая
        # coords_list = [[x_1,y_1],
        #                [x_2,y_2]
        #               ]
        # coords_list=sorted(coords_list,key=lambda x: x[0])
        # x_1, y_1 = coords_list[0][0], coords_list[0][1]
        # x_2, y_2 = coords_list[1][0], coords_list[1][1]

        typey = -1
        typex = -1

        # определяем тип х координаты
        if x_1 >= self.central_transition_right and x_2 <= self.right_transition_x:
            typex = 1  # обе x координаты в последней четверти (вторая справа от конвейера)

        elif x_1 >= self.perpendicular_conveyor_x_coord and x_2 <= self.central_transition_right:
            typex = 2  # обе x координаты в третьей четверти (первая справа от конвейера)

        elif x_1 >= self.central_transition_left and x_2 <= self.perpendicular_conveyor_x_coord:
            typex = 3  # обе x координаты во второй четверти (первая слева от конвейера)

        elif x_2 <= self.central_transition_left:
            typex = 4  # обе x координаты в первой четверти (вторая слева от конвейера)

        elif x_1 >= self.perpendicular_conveyor_x_coord and x_2 <= self.right_transition_x:
            typex = 5  # обе точки справа от конвейера

        elif x_2 <= self.perpendicular_conveyor_x_coord:
            typex = 6  # обе точки слева от конвейера

        elif x_2 >= self.perpendicular_conveyor_x_coord and x_1 <= self.perpendicular_conveyor_x_coord and x_2 <= self.right_transition_x:  # было  x_2 >= self.perpendicular_conveyor_x_coord and x_2 <= self.right_transition_x
            typex = 7  # по разные стороны от конвейера

        elif x_1 == self.x_max:
            typex = 8  # обе точки справа от конвейера в последнем ряду по х (отдельно стоящие стелажи справа в самом верху)

        elif x_2 == self.x_max:
            typex = 9  # одна точка справа от конвейера в последнем ряду по х (отдельно стоящие стелажи справа в самом верху)

        # определяем тип y координаты
        if max(y_1, y_2) <= self.foreman_zone_y_start:
            typey = 1  # обе до зоны бригадира

        elif max(y_1, y_2) <= self.parallel_conveyor_y_coord and min(y_1, y_2) >= self.foreman_zone_y_end:
            typey = 2  # обе между зоной бригадира и параллельным конвейером

        elif min(y_1, y_2) >= self.parallel_conveyor_y_coord and max(y_1, y_2) < self.perpendicular_conveyor_min_y_end:
            typey = 3  # обе выше параллельного конвейера и до конца перпендикулярного стеллажам конвейера

        elif min(y_1, y_2) >= self.perpendicular_conveyor_min_y_end:
            typey = 4  # обе выше конца перпендикулярного стеллажам конвейера

        elif max(y_1, y_2) <= self.parallel_conveyor_y_coord:
            typey = 5  # одна до зоны бригадира вторая между зоной бригадира и параллельным конвейером

        elif max(y_1, y_2) >= self.parallel_conveyor_y_coord and min(y_1, y_2) <= self.parallel_conveyor_y_coord:

            if min(y_1, y_2) >= self.foreman_zone_y_end:
                typey = 6  # одна выше параллельного конвейера, вторая между зоной бригадира и конвейером

            else:
                typey = 7  # одна выше параллельного конвейера, вторая ниже зоны бригадира

        if typex == -1 and typey == -1:
            print('Something went wrong with types')
            return -1, -1  # если не попало ни в какую зону -- странность

        return typex, typey

    def time_for_optimal_dist(self, x_1, y_1, floor_1, x_2, y_2, floor_2, speed=2.8 / 3.6, time_for_passing_conv=30,
                              time_for_passing_floor=10):

        if not self.coordinates_check(x_1, y_1, x_2, y_2):  # проверяем координаты
            print('Something went wrong with boundaries')
            return -1, -1

        if floor_1 == floor_2:  # ходим внутри одного этажа

            if x_1 == x_2 and y_1 == y_2:  # нет перехода, стоим у одной и той же ячейки
                return 0.0, 0.0

            # сортируем координаты, чтобы первая точка имели координату по х не больше, чем вторая
            coords_list = [[x_1, y_1],
                           [x_2, y_2]
                           ]
            coords_list = sorted(coords_list, key=lambda x: x[0])
            x_1, y_1 = coords_list[0][0], coords_list[0][1]
            x_2, y_2 = coords_list[1][0], coords_list[1][1]

            typex, typey = self.types_of_coordinates_on_the_same_floor(x_1, y_1, x_2,
                                                                       y_2)  # находим тип пары координат

            if ((abs(y_1 - y_2) == self.passage_diff or y_1 == y_2) and typex != 7) or ((
                                                                                                abs(y_1 - y_2) == self.passage_diff or y_1 == y_2) and typex == 7 and typey == 4):  # если в одном проходе (кроме случаев когда по разные стороны от конвейера или самого верхнего прохода)
                s = np.sqrt(((x_1 - x_2) * self.x_scale) ** 2 + ((y_1 - y_2 - 1) * self.y_scale) ** 2)
                return (s / speed) * 1_000_000.0, s  # идем просто по-диагонали

            elif typey in [6, 7] and typex in [3, 4,
                                               6]:  # если y-ки по разные стороны от параллельного конвейера, а x-ы в нижней половине

                if floor_1 not in self.no_transit_parallel_conv and floor_1 not in self.have_no_end_perpendicular_conveyor:  # если на этаже есть проход и через перпендикулярный конвейер, и через параллельный
                    if y_1 > y_2:
                        y_1, y_2 = y_2, y_1
                        x_1, x_2 = x_2, x_1

                    t1, s1 = self.time_for_optimal_dist(
                        x_1,
                        y_1,
                        floor_1,
                        self.parallel_conveyor_x_end,
                        self.parallel_conveyor_y_coord - 1,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    # t0, s0 - идем от прохода через параллельный конвейер, до конечной точки
                    t0, s0 = self.time_for_optimal_dist(
                        self.parallel_conveyor_x_end,
                        self.parallel_conveyor_y_coord + 1,
                        floor_1,
                        x_2,
                        y_2,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t1 = t1 + t0 + 2 * self.x_scale / speed * 1_000_000.0
                    s1 = s1 + s0 + 2 * self.x_scale

                    # проход через перпендикулярный конвейер на 87 у-ке
                    # идем от первой точки до перехода на 87 y-ке
                    t2, s2 = self.time_for_optimal_dist(
                        x_1,
                        y_1,
                        floor_1,
                        self.perpendicular_conveyor_x_coord - 1,
                        self.perpendicular_conveyor_transition,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    # идем от конца перпендикулярного конвейера до конечной точки
                    t0, s0 = self.time_for_optimal_dist(
                        self.perpendicular_conveyor_x_coord - 1,
                        self.perpendicular_conveyor_min_y_end,
                        floor_1,
                        x_2,
                        y_2,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t2 = t2 + t0 + (4 * self.x_scale / speed + time_for_passing_conv + (
                                self.perpendicular_conveyor_min_y_end - self.perpendicular_conveyor_transition) * self.y_scale / speed) * 1_000_000.0
                    s2 = s2 + s0 + 4 * self.x_scale + (
                                self.perpendicular_conveyor_min_y_end - self.perpendicular_conveyor_transition) * self.y_scale

                    # возвращаем минимальное из двух расстояний
                    if t1 <= t2:
                        return t1, s1
                    else:
                        return t2, s2

                elif floor_1 not in self.no_transit_parallel_conv and floor_1 in self.have_no_end_perpendicular_conveyor:  # если перпендикулярный конвейер идет через весь этаж

                    if y_1 > y_2:
                        y_1, y_2 = y_2, y_1
                        x_1, x_2 = x_2, x_1

                    t1, s1 = self.time_for_optimal_dist(
                        x_1,
                        y_1,
                        floor_1,
                        self.parallel_conveyor_x_end,
                        self.parallel_conveyor_y_coord - 1,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t0, s0 = self.time_for_optimal_dist(
                        self.parallel_conveyor_x_end,
                        self.parallel_conveyor_y_coord + 1,
                        floor_1,
                        x_2,
                        y_2,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t1 = t1 + t0 + 2 * self.x_scale / speed * 1_000_000.0
                    s1 = s1 + s0 + 2 * self.x_scale

                    return t1, s1

                elif floor_1 in self.no_transit_parallel_conv:  # если нет прохода через параллельный

                    if y_1 > y_2:
                        y_1, y_2 = y_2, y_1
                        x_1, x_2 = x_2, x_1

                    t2, s2 = self.time_for_optimal_dist(
                        x_1,
                        y_1,
                        floor_1,
                        self.perpendicular_conveyor_x_coord - 1,
                        self.perpendicular_conveyor_transition,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t0, s0 = self.time_for_optimal_dist(
                        self.perpendicular_conveyor_x_coord - 1,
                        self.perpendicular_conveyor_min_y_end,
                        floor_1,
                        x_2,
                        y_2,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t2 = t2 + t0 + (4 * self.x_scale / speed + time_for_passing_conv + (
                                self.perpendicular_conveyor_min_y_end - self.perpendicular_conveyor_transition) * self.y_scale / speed) * 1_000_000.0
                    s2 = s2 + s0 + 4 * self.x_scale + (
                                self.perpendicular_conveyor_min_y_end - self.perpendicular_conveyor_transition) * self.y_scale

                    return t2, s2

            else:
                if typex in [1, 2, 3, 4]:  # если оба x-а в одной и той же полосе
                    # ищем верхнюю и нижнюю границы полос
                    if typex == 1:
                        local_x_min = self.central_transition_right
                        local_x_max = self.right_transition_x
                    elif typex == 2:
                        local_x_min = self.perpendicular_conveyor_x_coord + 1
                        local_x_max = self.central_transition_right
                    elif typex == 3:
                        local_x_min = self.central_transition_left
                        local_x_max = self.perpendicular_conveyor_x_coord - 1
                    elif typex == 4:
                        local_x_min = self.x_min
                        local_x_max = self.central_transition_left
                    # берем манхэтенское расстояние и два минимума до границ
                    manh_dist = (x_2 - x_1) * self.x_scale + abs(y_2 - y_1) * self.y_scale
                    min_move_left = (x_1 - local_x_min) * self.x_scale
                    min_move_right = (local_x_max - x_2) * self.x_scale
                    return ((min(min_move_left, min_move_right) * 2 + manh_dist) / speed) * 1_000_000.0, (
                                min(min_move_left, min_move_right) * 2 + manh_dist)
                elif typex == 5 or typex == 6:  # если в одной половине, но в разных четвертях, и если в нижней половине, то нет прохода через конвейер
                    return (((x_2 - x_1) * self.x_scale + abs(y_2 - y_1) * self.y_scale) / speed) * 1_000_000.0, (
                                (x_2 - x_1) * self.x_scale + abs(y_2 - y_1) * self.y_scale)  # просто манхэтенское
                elif typex == 7:  # в разных половинах
                    # если оба y-ка выше чем конец перпендикулярного конвейера и этот конец есть
                    if y_1 >= self.perpendicular_conveyor_min_y_end and y_2 >= self.perpendicular_conveyor_min_y_end and floor_1 not in self.have_no_end_perpendicular_conveyor:
                        # идем до конвейера сдвигаясь в сторону второго y-ка, переходим через конвейер и идем до конечной точки
                        t, s = self.time_for_optimal_dist(
                            x_1,
                            y_1,
                            floor_1,
                            self.perpendicular_conveyor_x_coord - 1,
                            y_2,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t0, s0 = self.time_for_optimal_dist(
                            self.perpendicular_conveyor_x_coord + 1,
                            y_2,
                            floor_1,
                            x_2,
                            y_2,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t = t + t0 + 2 * self.x_scale / speed * 1_000_000.0
                        s = s + s0 + 2 * self.x_scale
                        return t, s
                    # если проход через перпендикулярный конвейер есть
                    elif floor_1 not in self.have_no_end_perpendicular_conveyor:
                        # путь через проход на 87 у-ке
                        t1, s1 = self.time_for_optimal_dist(
                            x_1,
                            y_1,
                            floor_1,
                            self.perpendicular_conveyor_x_coord - 1,
                            self.perpendicular_conveyor_transition,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t0, s0 = self.time_for_optimal_dist(
                            self.perpendicular_conveyor_x_coord + 1,
                            self.perpendicular_conveyor_transition,
                            floor_1,
                            x_2,
                            y_2,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t1 = t1 + t0 + (2 * self.x_scale / speed + time_for_passing_conv) * 1_000_000.0
                        s1 = s1 + s0 + 2 * self.x_scale

                        # путь через верхний конец
                        t2, s2 = self.time_for_optimal_dist(
                            x_1,
                            y_1,
                            floor_1,
                            self.perpendicular_conveyor_x_coord - 1,
                            self.perpendicular_conveyor_min_y_end,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t0, s0 = self.time_for_optimal_dist(
                            self.perpendicular_conveyor_x_coord + 1,
                            self.perpendicular_conveyor_min_y_end,
                            floor_1,
                            x_2,
                            y_2,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t2 = t2 + t0 + 2 * self.x_scale / speed * 1_000_000.0
                        s2 = s2 + s0 + 2 * self.x_scale
                        if (t1 <= t2):
                            return t1, s1
                        else:
                            return t2, s2
                    # если прохода в конце нет
                    else:
                        t1, s1 = self.time_for_optimal_dist(
                            x_1,
                            y_1,
                            floor_1,
                            self.perpendicular_conveyor_x_coord - 1,
                            self.perpendicular_conveyor_transition,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t0, s0 = self.time_for_optimal_dist(
                            self.perpendicular_conveyor_x_coord + 1,
                            self.perpendicular_conveyor_transition,
                            floor_1,
                            x_2,
                            y_2,
                            floor_2,
                            speed,
                            time_for_passing_conv,
                            time_for_passing_floor
                        )
                        t1 = t1 + t0 + (2 * self.x_scale / speed + time_for_passing_conv) * 1_000_000.0
                        s1 = s1 + s0 + 2 * self.x_scale
                        return t1, s1
                # если оба x-а в верхнем ряду, то проходим разницу по y плюс дважды до ячейки
                elif typex == 8:
                    return ((abs(y_1 - y_2) + 2) * self.y_scale / speed) * 1_000_000.0, (
                                abs(y_1 - y_2) + 2) * self.y_scale
                # если только одна в верхнем ряду, то доходим до точки на верхнем проходе и поднимаемся
                elif typex == 9:
                    t, s = self.time_for_optimal_dist(
                        x_1,
                        y_1,
                        floor_1,
                        self.right_transition_x,
                        y_2,
                        floor_2,
                        speed,
                        time_for_passing_conv,
                        time_for_passing_floor
                    )
                    t = t + (1 * self.x_scale / speed) * 1_000_000.0
                    s = s + 1 * self.x_scale
                    return t, s
        else:
            t1, s1 = self.time_for_optimal_dist(x_1, y_1, floor_1, (self.ladder_x_min + self.ladder_x_max) // 2,
                                                self.foreman_zone_y_start, floor_1, speed, time_for_passing_conv,
                                                time_for_passing_floor)
            t1 = t1 + (((
                                    self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_start) * self.y_scale / speed) * 1_000_000.0
            s1 = s1 + ((self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_start) * self.y_scale
            # f1 = self.time_for_optimal_dist(x_1, y_1, floor_1, (self.ladder_x_min + self.ladder_x_max) // 2, self.foreman_zone_y_start, floor_1, speed, time_for_passing_conv, time_for_passing_floor) \
            #    +(( ( self.ladder_y_min + self.ladder_y_max ) / 2 - self.foreman_zone_y_start) * self.y_scale / speed ) * 1_000_000

            t2, s2 = self.time_for_optimal_dist(x_1, y_1, floor_1, (self.ladder_x_min + self.ladder_x_max) // 2,
                                                self.foreman_zone_y_end, floor_1, speed, time_for_passing_conv,
                                                time_for_passing_floor)
            t2 = t2 + (((
                                    self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale / speed) * 1_000_000.0
            s2 = s2 + ((self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale
            # f2 = self.time_for_optimal_dist(x_1, y_1, floor_1, (self.ladder_x_min + self.ladder_x_max) // 2, self.foreman_zone_y_end, floor_1, speed, time_for_passing_conv, time_for_passing_floor) \
            #    + (( (self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale / speed )  * 1_000_000

            t3, s3 = self.time_for_optimal_dist(x_2, y_2, floor_2, (self.ladder_x_min + self.ladder_x_max) // 2,
                                                self.foreman_zone_y_start, floor_2, speed, time_for_passing_conv,
                                                time_for_passing_floor)
            t3 = t3 + (((
                                    self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_start) * self.y_scale / speed) * 1_000_000.0
            s3 = s3 + ((self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_start) * self.y_scale
            # f3 = self.time_for_optimal_dist(x_2, y_2, floor_2, (self.ladder_x_min + self.ladder_x_max) // 2, self.foreman_zone_y_start, floor_2, speed, time_for_passing_conv, time_for_passing_floor) \
            #    + (( (self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_start) * self.y_scale / speed ) * 1_000_000

            t4, s4 = self.time_for_optimal_dist(x_2, y_2, floor_2, (self.ladder_x_min + self.ladder_x_max) // 2,
                                                self.foreman_zone_y_end, floor_2, speed, time_for_passing_conv,
                                                time_for_passing_floor)
            t4 = t4 + (((
                                    self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale / speed) * 1_000_000.0
            s4 = s4 + ((self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale
            # f4 = self.time_for_optimal_dist(x_2, y_2, floor_2, (self.ladder_x_min + self.ladder_x_max) // 2, self.foreman_zone_y_end, floor_2, speed, time_for_passing_conv, time_for_passing_floor) \
            #    + (( (self.ladder_y_min + self.ladder_y_max) / 2 - self.foreman_zone_y_end) * self.y_scale / speed ) * 1_000_000
            if t1 <= t2:
                t, s = t1, s1
            else:
                t, s = t2, s2
            if t3 <= t4:
                t = t + t3
                s = s + s3
            else:
                t = t + t4
                s = s + s4
            t = t + time_for_passing_floor * abs(floor_1 - floor_2) * 1_000_000
            s = s + abs(floor_1 - floor_2) * self.length_of_stairs
            # return min(f1, f2) + min(f3, f4) + time_for_passing_floor * abs(floor_1 - floor_2) * 1_000_000
            return t, s

    def time(self, x_1, y_1, x_2, y_2):
        return self.time_for_optimal_dist(x_1, y_1, 3, x_2, y_2, 3)[0]

    def distance(self, x_1, y_1, x_2, y_2):
        return self.time_for_optimal_dist(x_1, y_1, 3, x_2, y_2, 3)[1]


def dist(p1: tuple, p2: tuple) -> float:
    warehouse_instance = Warehouse()
    return warehouse_instance.distance(p1[0], p1[1], p2[0], p2[1])


def lenght(path: list[tuple]) -> float:
    result = 0.0
    for i in range(len(path) - 1):
        result += dist(path[i], path[i + 1])
    return result


t0 = 1.0


class Otjig:
    def cool(self, step: int):
        self.temp = t0 * 0.99 ** step

    def otjig(self):
        swap1 = randint(1, len(self.cur) - 1)
        swap2 = randint(1, len(self.cur) - 1)
        new = self.cur.copy()
        new[swap1], new[swap2] = new[swap2], new[swap1]
        new_res = lenght(new)

        if new_res < self.cur_result or random() < exp((self.cur_result - new_res) / self.temp):
            self.cur_result = new_res
            self.cur = new

    def optimise(self, inp: list[tuple], start_point, iterations=1000) -> list[tuple]:
        self.cur = inp.copy()
        self.cur_result = lenght(self.cur)
        for i in range(iterations):
            self.cool(i + 1)
            self.otjig()
        result = self.cur.copy()
        result = [start_point] + result + [start_point]
        result_fin = []
        hor_lines = [2, 19, 38, 42, 64, 82]
        for i in range(0, len(result)):
            if i == len(result) - 1:
                result_fin.append(result[i])
            else:
                x = result[i][0]
                y = result[i][1]
                xn = result[i + 1][0]
                yn = result[i + 1][1]
                result_fin.append(result[i])
                if (x == xn or x + 2 == xn) and x % 3 == 1:
                    x += 1
                    result_fin.append((x, y))
                    while y > yn:
                        y -= 1
                        result_fin.append((x, y))
                    while y < yn:
                        y += 1
                        result_fin.append((x, y))
                else:
                    if (x == xn or xn + 2 == x) and x % 3 == 0:
                        x -= 1
                        result_fin.append((x, y))
                        while y > yn:
                            y -= 1
                            result_fin.append((x, y))
                        while y < yn:
                            y += 1
                            result_fin.append((x, y))
                    else:
                        hor_line = hor_lines[0]
                        for i in hor_lines:
                            if (max(i, y) - min(i, y) + max(i, yn) - min(yn, i)) < (
                                    max(hor_line, y) - min(hor_line, y) + max(hor_line, yn) - min(yn, hor_line)):
                                hor_line = i
                        if hor_line > y:
                            while y < hor_line:
                                y += 1
                                result_fin.append((x, y))
                        else:
                            while y > hor_line:
                                y -= 1
                                result_fin.append((x, y))
                        if xn % 3 == 1:
                            if x > xn:
                                while x != xn + 1:
                                    x -= 1
                                    result_fin.append((x, y))
                            else:
                                while x != xn + 1:
                                    x += 1
                                    result_fin.append((x, y))
                            if y > yn:
                                while y != yn:
                                    y -= 1
                                    result_fin.append((x, y))
                            if y < yn:
                                while y != yn:
                                    y += 1
                                    result_fin.append((x, y))
                        else:
                            if x > xn:
                                while x != xn - 1:
                                    x -= 1
                                    result_fin.append((x, y))
                            else:
                                while x != xn - 1:
                                    x += 1
                                    result_fin.append((x, y))
        return result_fin