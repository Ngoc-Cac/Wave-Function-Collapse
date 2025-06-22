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
    """
    Data Container to push to PriorityQueue. This container
    implements the `__lt__`, `__hash__` and `__eq__` methods for
    efficient organization in the queue.

    :param int index: The position of the cell in the grid. This index
        is given in the flattened grid and **not** as (row, col).
    :param Cell cell: The actual Cell object.
    """
    index: int
    cell: Cell

    def __lt__(self, other:'_CellDataContainer') -> bool:
        return self.cell.entropy < other.cell.entropy
    def __eq__(self, other: '_CellDataContainer') -> bool:
        return self.index == other.index
    
    def __hash__(self) -> int:
        return hash(self.index)

def _propogate(
    position: int,
    output_dimension: tuple[int, int],
    generated_img: list[Cell],
    non_collapse_queue: PriorityQueue[_CellDataContainer]
) -> bool:
    """
    Propogate state updates from the given position. The propogation
    works in four directions: up, down, left and right.

    :param int position: The position to propogate from. This should
        be given as if the grid is flattened and **not** a (row, col) pair.
    :param tuple[int, int] output_dimension: The actual dimension of the grid.
    :param list[Cell] generated_img: The flattened grid of cells.
    :param PriorityQueue[_CellDataContainer] non_collapse_queue: The current
        priority queue of uncollapsed cell. This is used to update the priority
        of existing cells after updating the state.
    :return bool: Whether or not all cells are still valid after updating.
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
        ):
            continue
        elif not generated_img[index].is_valid:
            return False
        
        non_collapse_queue.push(_CellDataContainer(index, generated_img[index]))

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

    This function is actually a generator that yields the state of the grid after
    propogation is done, the state is given as a numpy.NDArray that represents an
    image. It is made this way so that retrieving intermediate results is easier.
    See the example below for usage of this function:
    ```python
    >>> from wfc.cell_image import TileImage
    >>> from wfc._algos import _wfc
    >>> patterns = [TileImage(...) for tile in tileset] # load patterns
    >>> for grid_as_img in _wfc(patterns, (5, 5), False):
    ...     f'Draw image or something {grid_as_img}'
    >>> # This however won't give you the return value.
    >>> # There a few ways to do it. The easiest is creating a class wrapper and use yield from.
    ... class CustomGen:
    ...     def __init__(self, generator):
    ...         self.gen = generator
    ...     def __iter__(self):
    ...         self.result = yield from self.gen
    ... inner_gen = _wfc(patterns, (5, 5), False)
    ... gen = CustomGen(inner_gen)
    ... # If we don't want the intermediate results, just do nothing during iterating.
    ... for _ in gen:
    ...     pass
    ... # The final result can be retrieved from the result variable
    ... type(gen.result), len(gen.result)
    (tuple, 2)
    ```

    :param list[TileImage] patterns: The tileset to perform WFC on.
    :param tuple[int, int] output_dimension: The dimension of the output grid.
    :param bool repeat_until_success: Whether or not to reset the grid if one 
        of the cell become invalid.
    """
    intermediate_result = lambda: concat_grid(matrix, patterns[0].image.shape, output_dimension)
    success = False
    
    while not success:
        matrix = [Cell(patterns) for _ in range(output_dimension[0] * output_dimension[1])]
        min_index = rand.randint(0, output_dimension[0] * output_dimension[1] - 1)
        matrix[min_index].collapse()
        
        non_collapsed = PriorityQueue((
            _CellDataContainer(i, cell)
            for i, cell in enumerate(matrix) if not cell.is_collapsed
        ))
        _propogate(min_index, output_dimension, matrix, non_collapsed)

        yield intermediate_result()

        while not (success := all(cell.is_collapsed for cell in matrix)):
            temp = non_collapsed.pop()
            min_index, cell = temp.index, temp.cell

            cell.collapse()
            if not _propogate(min_index, output_dimension, matrix, non_collapsed): break

            yield intermediate_result()


        if not repeat_until_success: break
    return success, intermediate_result()