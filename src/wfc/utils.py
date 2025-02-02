import os

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure

from scipy.ndimage import rotate


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

def show_tiles(tiles) -> tuple[matplotlib.figure.Figure, np.ndarray[plt.Axes]]:
    rows = int(np.sqrt(len(tiles)))
    cols = int(np.ceil(len(tiles) / rows))
    fig, ax_arr = plt.subplots(rows, cols)
    if rows == 1:
        temp = np.ndarray((1, cols), dtype=object)
        temp[0] = np.array(ax_arr)
        ax_arr = temp

    for row in ax_arr:
        for ax in row: ax.axis('off')
    for i, tile in enumerate(tiles):
        ax_arr[(i - i % cols) // cols, i % cols].imshow(tile)
    return fig, ax_arr

def load_patterns(directory: str, rotate: bool = True) -> list[np.ndarray]:
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
                      rotate: bool = False) -> list[np.ndarray]:
    image = cv2.cvtColor(cv2.imread(image_filepath), cv2.COLOR_BGR2RGB)

    patterns = []
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            row_indices = [[(i + offset) % image.shape[0]] for offset in range(n_pixels)]
            col_indices = [(j + offset) % image.shape[1] for offset in range(n_pixels)]
            patterns.append(image[row_indices, col_indices])

    if rotate: patterns.extend(_augment_by_rotation(patterns))
    return patterns