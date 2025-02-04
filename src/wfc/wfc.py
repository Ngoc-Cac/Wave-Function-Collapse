import random as rand
import numpy as np

from wfc.cell_image import (
    Cell,
    Direction,
    TileImage
)

from typing import (
    Generator,
    Iterable,
    Literal
)


def concat_grid(tiles_grid: list[Cell],
                tiles_shape: tuple[int, int, Literal[3]],
                dimension: tuple[int, int]) -> np.ndarray:
    """
    Concatenate a grid of Cell objects into a single image.

    This asumes that every Cell has a superposition state, else its\
        image representation will be filled with black.

    ## Parameters:
        tiles_grid: list of Cell objects to concatenate
        tiles_shape: the dimension of a Cell
        dimension: dimension of the final image after concatenation

    ## Return
    A `numpy.ndarray` of shape `(int, int, 3)`
    """
    failure_cell = np.zeros(tiles_shape, dtype='uint8')
    row_pixels = []
    for i in range(dimension[0]):
        row = i * dimension[1]
        temp = np.concatenate([cell.image if cell.image is not None else failure_cell
                               for cell in tiles_grid[row:row + dimension[1]]], axis=1)
        row_pixels.append(temp)
    return np.concatenate(row_pixels)

def _propogate(position: int,
               output_dimension: tuple[int, int],
               generated_img: list[Cell]) -> bool:
    """
    Propogate a wave from a position
    """
    row = (position - position % output_dimension[1]) // output_dimension[1]
    col = position % output_dimension[1]

    stack: list[tuple[int, Direction]] = []
    if row - 1 > -1:
        stack.append(((row - 1) * output_dimension[1] + col, Direction.UP))
    if row + 1 < output_dimension[0]:
        stack.append(((row + 1) * output_dimension[1] + col, Direction.DOWN))
    if col - 1 > -1:
        stack.append((row * output_dimension[1] + col - 1, Direction.LEFT))
    if col + 1 < output_dimension[1]:
        stack.append((row * output_dimension[1] + col + 1, Direction.RIGHT))

    while stack:
        index, direction = stack.pop()
        row = (index - index % output_dimension[1]) // output_dimension[1]
        col = index % output_dimension[1]

        match direction:
            case Direction.UP:
                other_index = (row + 1) * output_dimension[1] + col
            case Direction.DOWN:
                other_index = (row - 1) * output_dimension[1] + col
            case Direction.LEFT:
                other_index = index + 1
            case Direction.RIGHT:
                other_index = index - 1
        if not generated_img[index].update_options(generated_img[other_index], direction):
            continue
        
        if not generated_img[index].is_valid: return False
        if row - 1 > -1:
            stack.append(((row - 1) * output_dimension[1] + col, Direction.UP))
        if row + 1 < output_dimension[0]:
            stack.append(((row + 1) * output_dimension[1] + col, Direction.DOWN))
        if col - 1 > -1:
            stack.append((row * output_dimension[1] + col - 1, Direction.LEFT))
        if col + 1 < output_dimension[1]:
            stack.append((row * output_dimension[1] + col + 1, Direction.RIGHT))

    return all(cell.is_valid for cell in generated_img)

def _wave_function_collapse(
        patterns: list[TileImage],
        output_dimension: tuple[int, int], *,
        repeat_until_success: bool = True
    ) -> Generator[np.ndarray, None, tuple[bool, np.ndarray]]:
    """
    Wave function collapse on a set of tiles. In order to work properly,\
        this set should contain square tiles with the same shape.

    ## Parameters
    """
    success = False
    while not success:
        matrix: list[Cell] = [Cell(patterns) for _ in range(output_dimension[0] * output_dimension[1])]
        min_index = rand.randint(0, output_dimension[0] * output_dimension[1] - 1)
        matrix[min_index].collapse()
        _propogate(min_index, output_dimension, matrix)

        while not all(cell.is_collapsed for cell in matrix):
            yield concat_grid(matrix, patterns[0].image.shape, output_dimension)

            min_index, _ = min([(i, cell.entropy) for i, cell in enumerate(matrix) if not cell.is_collapsed],
                               key=lambda tup: tup[1])
            matrix[min_index].collapse()
            if not _propogate(min_index, output_dimension, matrix): break

        yield concat_grid(matrix, patterns[0].image.shape, output_dimension)

        success = all(cell.is_collapsed for cell in matrix)
        if not repeat_until_success: break
    return success, concat_grid(matrix, patterns[0].image.shape, output_dimension)

class CollapsedError(Exception):
    """
    Exception thrown when WFC has already collapsed for the curretn configuration
    """

class WFC:
    __slots__ = '_generator', '_output_dim',\
                '_patterns', '_repeat_til_success',\
                '_need_update', '_return_val'
    def __init__(self, output_dimension: tuple[int, int],
                 patterns: Iterable[TileImage], *,
                 repeat_until_success: bool = True):
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

        self._output_dim = output_dimension
        self._patterns = list(patterns)
        self._repeat_til_success = repeat_until_success
        self._need_update = False

        self._init_gen()

    @property
    def output_dimension(self) -> tuple[int, int]:
        return self._output_dim
    @output_dimension.setter
    def outpu_dimension(self, new_dim: tuple[int, int]):
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

    def _init_gen(self):
        self._generator = _wave_function_collapse(self._patterns, self._output_dim,
                                                  repeat_until_success=self._repeat_til_success)
        self._need_update = False

    def run(self, restart: bool = False) -> tuple[bool, np.ndarray]:
        if self._need_update or restart: self._init_gen()
        ignore = None
        for ignore in self: pass
        
        if ignore is None:
            err_msg = "The current configuration for Wave Function Collapse has already" +\
                      " been run. Set restart = True for rerun."
            raise CollapsedError(err_msg)
        return self._return_val

    def __iter__(self)\
        -> Generator[np.ndarray, None, tuple[bool, np.ndarray]]:
        if self._need_update: self._init_gen()
        self._return_val = yield from self._generator
        return self._return_val
    
    def __next__(self) -> np.ndarray:
        return next(self._generator)