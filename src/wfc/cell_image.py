import random as rand
from enum import Enum

import numpy as np

from typing import Iterable, Optional

class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

class CellImage:
    __slots__ = '_collapsed', '_img', '_options', '_recur_depth'
    def __init__(self, patterns: Iterable[np.ndarray]):
        self._options = list(patterns)
        self._collapsed = False
        self._img = None

    @property
    def entropy(self) -> float:
        if not len(self._options): return np.inf
        return -np.log2(1 / len(self._options))
    @property
    def image(self) -> Optional[np.ndarray]:
        if not len(self._options): return None
        elif self._img is None:
            image = np.ndarray(self._options[0].shape)
            image[:] = np.mean(np.mean(self._options, axis=0), axis=(0, 1))
            return image.astype(int)
        else: return self._img
    @property
    def is_collapsed(self) -> bool:
        return self._collapsed
    @property
    def is_valid(self) -> bool:
        return bool(len(self._options))

    def update_options(self, cell_image: 'CellImage', direction: Direction) -> bool:
        new_options = []
        for option in self._options:
            overlap_able = False
            for other_opt in cell_image._options:
                if (
                    ((direction == Direction.UP) and (option[-1] == other_opt[0]).all()) or\
                    ((direction == Direction.DOWN) and (option[0] == other_opt[-1]).all()) or\
                    ((direction == Direction.LEFT) and (option[:, -1] == other_opt[:, 0]).all()) or\
                    ((direction == Direction.RIGHT) and (option[:, 0] == other_opt[:, -1]).all())
                ):
                    overlap_able = True
                    break
            if overlap_able: new_options.append(option)

        updated = len(new_options) != len(self._options)
        self._options = new_options
        if len(self._options) == 1: self.collapse()
        return updated

    def collapse(self):
        self._img = rand.choice(self._options)
        self._options = [self._img]
        self._collapsed = True