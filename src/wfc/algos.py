import random as rand

from dataclasses import dataclass

from .cell_image import (
    Cell,
    Direction,
    TileImage
)
from .priority_queue import PriorityQueue
from .utils import concat_grid


from numpy.typing import NDArray
from typing import (
    Generator,
)


@dataclass
class _CellDataContainer:
    index: int
    cell: Cell

    def __lt__(self, other:'_CellDataContainer') -> bool:
        return self.cell.entropy < other.cell.entropy
    def __eq__(self, other: '_CellDataContainer') -> bool:
        return self.index == other.index
    
    def __hash__(self) -> int:
        return hash(self.index)

def _propogate(position: int,
               output_dimension: tuple[int, int],
               generated_img: list[Cell],
               non_collapse_queue: PriorityQueue[_CellDataContainer]) -> bool:
    """
    Propogate a wave from a position
    """
    col = position % output_dimension[1]
    row = (position - col) // output_dimension[1]

    stack: list[tuple[int, int, int, int, Direction]] = []
    if row - 1 > -1:
        stack.append((row - 1, col, row, col, Direction.UP))
    if row + 1 < output_dimension[0]:
        stack.append((row + 1, col, row, col, Direction.DOWN))
    if col - 1 > -1:
        stack.append((row, col - 1, row, col, Direction.LEFT))
    if col + 1 < output_dimension[1]:
        stack.append((row, col + 1, row, col, Direction.RIGHT))

    while stack:
        row, col, other_row, other_col, direction = stack.pop()
        
        index = row * output_dimension[1] + col
        other_index = other_row * output_dimension[1] + other_col
        if (
            generated_img[index].is_collapsed or\
            not generated_img[index].update_options(generated_img[other_index], direction)
        ): continue
        non_collapse_queue.push(_CellDataContainer(index, generated_img[index]))

        if not generated_img[index].is_valid: return False
        if row - 1 > -1:
            stack.append((row - 1, col, row, col, Direction.UP))
        if row + 1 < output_dimension[0]:
            stack.append((row + 1, col, row, col, Direction.DOWN))
        if col - 1 > -1:
            stack.append((row, col - 1, row, col, Direction.LEFT))
        if col + 1 < output_dimension[1]:
            stack.append((row, col + 1, row, col, Direction.RIGHT))

    return all(cell.is_valid for cell in generated_img)

def _wfc(
        patterns: list[TileImage],
        output_dimension: tuple[int, int],
        repeat_until_success: bool
    ) -> Generator[NDArray, None, tuple[bool, NDArray]]:
    """
    Wave function collapse on a set of tiles. In order to work properly,
    this set should contain square tiles with the same shape.

    """
    intermediate_result = lambda: concat_grid(matrix, patterns[0].image.shape, output_dimension)
    success = False
    
    while not success:
        matrix = [Cell(patterns) for _ in range(output_dimension[0] * output_dimension[1])]
        min_index = rand.randint(0, output_dimension[0] * output_dimension[1] - 1)
        matrix[min_index].collapse()
        non_collapsed = PriorityQueue((_CellDataContainer(i, cell) for i, cell in enumerate(matrix)
                                       if not cell.is_collapsed))
        _propogate(min_index, output_dimension, matrix, non_collapsed)

        yield intermediate_result()

        while not all(cell.is_collapsed for cell in matrix):
            temp = non_collapsed.pop()
            min_index, cell = temp.index, temp.cell

            cell.collapse()
            if not _propogate(min_index, output_dimension, matrix, non_collapsed): break

            yield intermediate_result()


        success = all(cell.is_collapsed for cell in matrix)
        if not repeat_until_success: break
    return success, intermediate_result()