import random as rand
import numpy as np

from dataclasses import dataclass

from utilities.PriorityQueue import PriorityQueue
from utilities.utils import concat_grid
from wfc.cell_image import (
    Cell,
    Direction,
    TileImage
)

from numpy.typing import NDArray
from typing import (
    Generator,
    Iterable
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
    Wave function collapse on a set of tiles. In order to work properly,\
        this set should contain square tiles with the same shape.

    ## Parameters
    """
    intermediate_result = lambda: concat_grid(matrix, patterns[0].image.shape, output_dimension)
    success = False
    
    while not success:
        matrix: list[Cell] = [Cell(patterns) for _ in range(output_dimension[0] * output_dimension[1])]
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

class CollapsedError(Exception):
    """
    Exception thrown when WFC has already collapsed for the curretn configuration
    """

class WFC:
    __slots__ = '_generator', '_need_update',\
                '_output_dim', '_patterns',\
                '_repeat_til_success', '_rerun',\
                '_return_val'
    def __init__(self, output_dimension: tuple[int, int],
                 patterns: Iterable[TileImage], *,
                 repeat_until_success: bool = True,
                 rerun: bool = False):
        if not isinstance(output_dimension, tuple) or\
           len(output_dimension) != 2 or\
           any((not isinstance(i, int)) for i in output_dimension):
            raise TypeError(f"Expected a tuple of two int: {output_dimension}")
        elif any((dim < 1) for dim in output_dimension):
            raise ValueError("Dimension must be larger than 0")
        if any((not isinstance(tile, TileImage) for tile in patterns)):
            raise TypeError("Expected an Iterable of TileImage")
        if not isinstance(repeat_until_success, bool):
            raise TypeError('repeat_until_success must be a bool')
        if not isinstance(rerun, bool):
            raise TypeError('rerun must be a bool')

        self._output_dim = output_dimension
        self._patterns = list(patterns)
        self._repeat_til_success = repeat_until_success
        self._rerun = rerun
        self._need_update = True
        self._return_val = None

    @property
    def output_dimension(self) -> tuple[int, int]:
        return self._output_dim
    @output_dimension.setter
    def output_dimension(self, new_dim: tuple[int, int]):
        if not isinstance(new_dim, tuple) or len(new_dim) != 2 or\
           any((not isinstance(i, int)) for i in new_dim):
            raise TypeError(f"Expected a tuple of two int: {new_dim}")
        elif any((dim < 1) for dim in new_dim):
            raise ValueError("Dimension must be larger than 0")
        self._output_dim = new_dim
        self._need_update = True

    @property
    def patterns(self) -> Iterable[TileImage]:
        return iter(self._patterns)
    @patterns.setter
    def patterns(self, new_patterns: Iterable[TileImage]):
        if any((not isinstance(tile, TileImage) for tile in new_patterns)):
            raise TypeError("Expected an Iterable of TileImage")
        self._patterns = list(new_patterns)
        self._need_update = True

    @property
    def repeat_until_success(self) -> bool:
        return self._repeat_til_success
    @repeat_until_success.setter
    def repeat_until_success(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError('repeat value must be a bool')
        self._repeat_til_success = True
        self._need_update = True

    @property
    def rerun(self) -> bool:
        return self._rerun
    @rerun.setter
    def rerun(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError('rerun must be a bool')
        self._rerun = value
        if not self._return_val is None:
            self._need_update = True

    @property
    def wfc_result(self) -> tuple[bool, NDArray]:
        if self._return_val is None:
            image = NDArray(self._patterns[0].image.shape)
            image[:] = np.mean(np.mean([tile.image for tile in self._patterns], axis=0), axis=(0, 1))
            return False, image.astype('uint8')
        else:
            return self._return_val

    def _init_gen(self):
        self._generator = _wfc(self._patterns, self._output_dim,
                               self._repeat_til_success)
        self._return_val = None
        self._need_update = False

    def run(self) -> tuple[bool, NDArray]:
        if self._need_update: self._init_gen()
        prev_result = self._return_val
        for _ in self: pass
        
        if self._return_val is None:
            self._return_val = prev_result
            err_msg = "The current configuration for Wave Function Collapse has already" +\
                      " been collapsed. Consider setting rerun = True to rerun."
            raise CollapsedError(err_msg)
        return self._return_val

    def __iter__(self)\
        -> Generator[NDArray, None, tuple[bool, NDArray]]:
        # if self._need_update: self._init_gen()
        # self._return_val = yield from self._generator
        # return self._return_val
        return self
    
    def __next__(self) -> NDArray:
        if self._need_update: self._init_gen()
        try:
            return next(self._generator)
        except StopIteration as exc:
            self._return_val = exc.value
            if self._rerun: self._need_update = True
            raise exc