from scripts.algorithm.optimiser import Otjig, dist
from scripts.models.selection_request import SelectionRequest
from scripts.models.warehouse_on_db import Warehouse


def find_nearest(wh: Warehouse, sku: int, count: int) -> list:
    result = list()

    cells = wh.db.get_all_cells(f'SELECT cell_id FROM Warehouse WHERE sku={sku}')

    for cell in cells:
        pass
    # cells = [(c[0][0], c[0][1]) for c in wh.db.get_by_prompt(f'SELECT x, y FROM Cells WHERE id={cells[]}')]

    return result


def trans(wh: Warehouse, req: SelectionRequest) -> list:
    otj = Otjig()
    start = wh.start_cords
    points = list()

    for pair in req.get_data():
        product, count = pair
        cells = find_nearest(wh, product.sku, count)
        points += cells

    return {'cells': otj.optimise(points, start)}
