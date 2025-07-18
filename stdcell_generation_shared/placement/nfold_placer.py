logger = logging.getLogger('sivista_app')

class TransistorPlacer:
    """
    Interface definition of a transistor placement algorithm.
    """

    def place(self, transistors: Iterable[Transistor]) -> Cell:
        pass


class NFoldTransistorPlacer(TransistorPlacer):
    """
    This placement engine is a wrapper around a cell placement to generate a folded placement.
    """

    def __init__(self):
        pass
        
    def fold_placement(self, single_line_placement, height_req=1) -> Cell:
        logger.info(f'{height_req - 1} Fold Placer')
        placement = single_line_placement
        logger.debug(f'Placement before folding:\n{placement.upper}\n{placement.lower}')

        cells = np.array([placement.upper, placement.lower], dtype=object)
        pad_width = (height_req - cells.shape[1] % height_req) % height_req
        cells = np.pad(cells, ((0, 0), (0, pad_width)), mode='constant', constant_values=None)
        cells = np.vstack(
            [block if i % 2 != 0 else np.array([b[::-1] for b in block[::-1]]) for i, block in enumerate(np.hsplit(cells, height_req)[::-1])]
        )
        for i in range(len(cells)):
            if (i // 2) % 2 == 0:
                for j in range(len(cells[i])):
                    if not cells[i][j]:
                        continue
                    cells[i][j].source_net, cells[i][j].drain_net = cells[i][j].drain_net, cells[i][j].source_net

        if height_req > 1:
            new_placement = CellMultiHeight(
                width=len(cells[0]),
                height=len(cells),
            )
            new_placement.cells = cells
        return new_placement