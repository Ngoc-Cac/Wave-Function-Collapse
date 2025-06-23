import os

import numpy as np
import matplotlib.pyplot as plt

from PIL import Image
from matplotlib.axes import Axes
from scipy.ndimage import rotate

from .cell_image import (
    Direction,
    TileImage,
    Cell
)

from numpy.typing import NDArray
from typing import (
    Iterable,
    Literal,
    Optional
)


def _augment_by_rotation(patterns: list[NDArray]) -> list[NDArray]:
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

def concat_grid(
    tiles_grid: list[Cell],
    tiles_shape: tuple[int, int, Literal[3]],
    dimension: tuple[int, int]
) -> NDArray:
    """
    Concatenate a grid of Cell objects into a single image.

    This asumes that every Cell has a superposition state, else its
    image representation will be filled with black.

    :param list[Cell] tiles_grid: List of Cell objects to concatenate.
    :param tuple[int, int, Literal[3]] tiles_shape: The dimension of a Cell.
    :param tuple[int, int] dimension: Dimension of the output image.
    :return `numpy.NDArray`: An RGB image as a numpy array.
    """
    failure_cell = np.zeros(tiles_shape, dtype='uint8')
    row_pixels = []
    for i in range(dimension[0]):
        row = i * dimension[1]
        temp = np.concatenate([cell.image if cell.image is not None else failure_cell
                               for cell in tiles_grid[row:row + dimension[1]]], axis=1)
        row_pixels.append(temp)
    return np.concatenate(row_pixels)

def show_tiles(
    images: Iterable[NDArray], *,
    ax: Optional[Axes] = None
) -> Axes:
    """
    Show a list of tiles in a grid pattern.

    :param Iterable[NDArray] images: List of tiles as RGB images.
    :param matplotlib.axes.Axes, optional ax: Axes to draw on. This is
        `None` by default, which will draw on the default Axes instead.
    :return matplotlib.axes.Axes: The axes that was drawn on.
    """
    rows = int(np.sqrt(len(images)))
    cols = int(np.ceil(len(images) / rows))
    n_pix = list(images)[0].shape[0]

    grid = 255 * np.ones((n_pix * rows + rows - 1, n_pix * cols + cols - 1, 3), dtype='uint8')
    
    for i, image in enumerate(images):
        col = i % cols
        row = (i - col) // cols
        row, col = row * (n_pix + 1), col * (n_pix + 1)
        grid[row:(row + n_pix), col:(col + n_pix)] = image

    if ax is None: ax = plt.gca()
    ax.imshow(grid)
    ax.axis('off')
    return ax


def load_patterns(
    directory: str,
    rotate: bool = True
) -> list[NDArray]:
    """
    Load a list of numpy.NDArray representing the tiles and its rotated version.
    A directory containing the png images of the tile should be given.

    :param str directory: Path to directory containing the images of the tiles.
    :param bool, optional rotate: Where or not to augment the images by rotation.
        This is `True` by default.
    :return list[NDArray]: A list of images.
    """
    patterns = []
    for path in os.listdir(directory):
        if path[-3:] == 'png':
            patterns.append(np.array(
                Image.open(os.path.join(directory, path))
                     .convert('RGB')
            ))
    if rotate: patterns.extend(_augment_by_rotation(patterns))
    return patterns

def generate_patterns(
    image_filepath: str,
    n_pixels: int = 3,
    rotate: bool = False
) -> list[TileImage]:
    """
    Generate a list of tiles from a given image based on the overlapping model.

    :param str image_filepath: Path to image.
    :param int, optional n_pixels: Dimension of tiles in pixels. This is `3` by
        default.
    :param bool, optional rotate: Whether or not to augment the tiles by rotation.
        This is `False` by default.
    
    :return list[TileImage]: The generated tiles.
    """
    image = np.array(Image.open(image_filepath).convert('RGB'))

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
    def image(self) -> NDArray:
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