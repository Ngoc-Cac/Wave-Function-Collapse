import os

import cv2
import numpy as np
import matplotlib.figure
import matplotlib.pyplot as plt

from scipy.ndimage import rotate

from wfc.cell_image import (
    Direction,
    TileImage,
    Cell
)

from typing import (
    Iterable,
    Literal)


def _augment_by_rotation(patterns: list[np.ndarray]) -> list[np.ndarray]:
    rotated_patterns = []
    for pattern in patterns:
        ninety = rotate(pattern, 90)
        if (ninety == pattern).all(): continue

        eighty = rotate(pattern, 180)
        twensev = rotate(pattern, 270)

        rotated_patterns.append(ninety)
        if not (eighty == pattern).all():
            rotated_patterns.append(eighty)
        if not (ninety == twensev).all():
            rotated_patterns.append(twensev)
    return rotated_patterns

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

def show_tiles(images: Iterable[np.ndarray], *, fig = matplotlib.figure.Figure)\
    -> tuple[matplotlib.figure.Figure, np.ndarray[plt.Axes]]:
    rows = int(np.sqrt(len(images)))
    cols = int(np.ceil(len(images) / rows))
    if fig is None:
        fig, ax_arr = plt.subplots(rows, cols)
    else:
        ax_arr = fig.subplots(rows, cols)
    if rows == 1:
        temp = np.ndarray((1, cols), dtype=object)
        temp[0] = np.array(ax_arr)
        ax_arr = temp

    for row in ax_arr:
        for ax in row: ax.axis('off')
    for i, image in enumerate(images):
        ax_arr[(i - i % cols) // cols, i % cols].imshow(image)
    return fig, ax_arr


def load_patterns(directory: str, rotate: bool = True)\
    -> list[np.ndarray]:
    """
    Load a list of numpy.ndarray representing the tiles and its rotated version.
    
    A directory containing the png images of the tile should be given.

    ## Parameters:
        directory: a directory containing png's representing tiles.
    """
    patterns = []
    for path in os.listdir(directory):
        if path[-3:] == 'png':
            patterns.append(cv2.cvtColor(cv2.imread(os.path.join(directory, path)),
                                         cv2.COLOR_BGR2RGB))
    if rotate: patterns.extend(_augment_by_rotation(patterns))
    return patterns

def generate_patterns(image_filepath: str,
                      n_pixels: int = 3,
                      rotate: bool = False)\
    -> list[TileImage]:
    image = cv2.cvtColor(cv2.imread(image_filepath), cv2.COLOR_BGR2RGB)

    unique_patterns = {}
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            row_indices = [[(i + offset) % image.shape[0]] for offset in range(n_pixels)]
            col_indices = [(j + offset) % image.shape[1] for offset in range(n_pixels)]
            
            sub_image = image[row_indices, col_indices]
            temp_key = tuple(sub_image.flatten())
            if temp_key in unique_patterns: unique_patterns[temp_key][1] += 1
            else: unique_patterns[temp_key] = [sub_image, 1]

    if rotate: 
        for rotated_pattern in _augment_by_rotation([value[0] for value in unique_patterns.values()]):
            temp_key = tuple(rotated_pattern.flatten())
            unique_patterns[temp_key] = [rotated_pattern, 1]
    return [_OverlappingModel_TileImage(*value) for value in unique_patterns.values()]


class _OverlappingModel_TileImage(TileImage):
    @TileImage.image.getter
    def image(self) -> np.ndarray:
        image = np.ndarray((1, 1, 3), dtype='uint8')
        image[0, 0] = self._pattern[0, 0]
        return image
    
    def is_adjacent_to(self, tile: '_OverlappingModel_TileImage', direction: Direction) -> bool:
        match direction:
            case Direction.UP:
                result = (self._pattern[1:] == tile._pattern[0:-1]).all()
            case Direction.DOWN:
                result = (self._pattern[0:-1] == tile._pattern[1:]).all()
            case Direction.LEFT:
                result = (self._pattern[:, 1:] == tile._pattern[:, 0:-1]).all()
            case Direction.RIGHT:
                result = (self._pattern[:, 0:-1] == tile._pattern[:, 1:]).all()
            case _:
                raise ValueError("Weird direction passed")
        return result