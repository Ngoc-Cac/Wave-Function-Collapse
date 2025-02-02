import random as rand
import numpy as np

from wfc.cell_image import Direction, CellImage

from typing import Callable, Literal, Optional


def concat_grid(tiles_grid: list[CellImage],
                tiles_shape: tuple[int, int, Literal[3]],
                dimension: tuple[int, int]) -> np.ndarray:
    """
    Concatenate a grid of CellImage objects into a single image.

    This asumes that every CellImage has a superposition state, else its\
        image representation will be filled with black.

    ## Parameters:
        tiles_grid: list of CellImage objects to concatenate
        tiles_shape: the dimension of a CellImage
        dimension: dimension of the final image after concatenation

    ## Return
    A `numpy.ndarray` of shape `(int, int, 3)`
    """
    failure_cell = np.zeros(tiles_shape, dtype=int)
    row_pixels = []
    for i in range(dimension[0]):
        row = i * dimension[1]
        temp = np.concatenate([cell.image if cell.image is not None else failure_cell
                               for cell in tiles_grid[row:row + dimension[1]]], axis=1)
        row_pixels.append(temp)
    return np.concatenate(row_pixels)

def _propogate(position: int,
               output_dimension: tuple[int, int],
               generated_img: list[CellImage]) -> bool:
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

def wave_function_collapse(
        patterns: list[np.ndarray],
        output_dimension: tuple[int, int], *,
        repeat_until_success: bool = True,
        collapse_update_func: Optional[Callable[[np.ndarray], None]] = None
    ) -> tuple[bool, np.ndarray]:
    """
    Wave function collapse on a set of tiles. In order to work properly,\
        this set should contain square tiles with the same shape.

    ## Parameters
    """
    success = False
    while not success:
        matrix: list[CellImage] = [CellImage(patterns) for _ in range(output_dimension[0] * output_dimension[1])]
        min_index = rand.randint(0, output_dimension[0] * output_dimension[1] - 1)
        matrix[min_index].collapse()
        _propogate(min_index, output_dimension, matrix)

        while not all(cell.is_collapsed for cell in matrix):
            if collapse_update_func:
                collapse_update_func(concat_grid(matrix, patterns[0].shape, output_dimension))

            min_index, _ = min([(i, cell.entropy) for i, cell in enumerate(matrix) if not cell.is_collapsed],
                               key=lambda tup: tup[1])
            matrix[min_index].collapse()
            if not _propogate(min_index, output_dimension, matrix): break

        if collapse_update_func:
            collapse_update_func(concat_grid(matrix, patterns[0].shape, output_dimension))

        success = all(cell.is_collapsed for cell in matrix)
        if not repeat_until_success: break
    return success, concat_grid(matrix, patterns[0].shape, output_dimension)