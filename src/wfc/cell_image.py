import random as rand
from enum import Enum

import numpy as np

from typing import Iterable, Optional

class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

class TileImage:
    __slots__ = '_pattern', '_frequency'
    def __init__(self, pattern: np.ndarray, frequency: int):
        self._pattern = pattern
        self._frequency = frequency

    @property
    def frequency(self) -> int:
        return self._frequency
    @property
    def image(self) -> np.ndarray:
        return self._pattern
    
    def is_adjacent_to(self, tile: 'TileImage', direction: Direction) -> bool:
        """
        Can this tile be adjacent in the `direction` to `tile`
        """
        match direction:
            case Direction.UP:
                result = (self._pattern[-1] == tile._pattern[0]).all()
            case Direction.DOWN:
                result = (self._pattern[0] == tile._pattern[-1]).all()
            case Direction.LEFT:
                result = (self._pattern[:, -1] == tile._pattern[:, 0]).all()
            case Direction.RIGHT:
                result = (self._pattern[:, 0] == tile._pattern[:, -1]).all()
            case _:
                raise ValueError("Weird direction passed")
        return result

class Cell:
    __slots__ = '_collapsed', '_options'
    def __init__(self, patterns: Iterable[TileImage]):
        self._options = list(patterns)
        self._collapsed = False

    @property
    def entropy(self) -> float:
        """
        entropy = log(total_count) - sigma weight_i * log(weight_i)
        """
        if not len(self._options): return np.inf

        total = sum(tile.frequency for tile in self._options)
        return np.log2(total) - sum(tile.frequency * np.log2(tile.frequency) for tile in self._options) / total
    @property
    def image(self) -> Optional[np.ndarray]:
        if not len(self._options): return None
        elif self._collapsed: return self._options[0].image
        else:
            image = np.ndarray(self._options[0].image.shape)
            image[:] = np.mean(np.mean(self._options, axis=0), axis=(0, 1))
            return image.astype('uint8')
    @property
    def is_collapsed(self) -> bool: return self._collapsed
    @property
    def is_valid(self) -> bool: return bool(len(self._options))

    def update_options(self, cell_image: 'Cell', direction: Direction) -> bool:
        new_options = []
        for option in self._options:
            for other_opt in cell_image._options:
                if option.is_adjacent_to(other_opt, direction):
                    new_options.append(option)
                    break

        updated = len(new_options) != len(self._options)
        self._options = new_options
        if len(self._options) == 1: self.collapse()
        return updated

    def collapse(self):
        counts = [tile.frequency for tile in self._options]
        self._options = rand.sample(self._options, 1, counts=counts)
        self._collapsed = True