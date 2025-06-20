import random as rand

from enum import Enum

import numpy as np

from numpy.typing import NDArray
from typing import (
    Iterable,
    Optional
)

class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class TileImage:
    __slots__ = '_pattern', '_frequency'
    def __init__(self, pattern: NDArray, frequency: int):
        if not isinstance(frequency, int):
            raise TypeError("frequency must be a positive integer...")
        elif frequency <= 0:
            raise ValueError("frequency must be a positive integer...")

        self._pattern = pattern
        self._frequency = frequency

    @property
    def frequency(self) -> int:
        return self._frequency

    @property
    def image(self) -> NDArray:
        return self._pattern
    
    def is_adjacent_to(self, tile: 'TileImage', direction: Direction) -> bool:
        """
        Can this tile be adjacent in the `direction` to `tile`
        """
        if direction == Direction.UP:
            result = (self._pattern[-1] == tile._pattern[0]).all()
        elif direction == Direction.DOWN:
            result = (self._pattern[0] == tile._pattern[-1]).all()
        elif direction == Direction.LEFT:
            result = (self._pattern[:, -1] == tile._pattern[:, 0]).all()
        elif direction == Direction.RIGHT:
            result = (self._pattern[:, 0] == tile._pattern[:, -1]).all()
        else:
            raise ValueError("Weird direction passed")
        return result


class Cell:
    """
    An uncollapse cell within a grid. A cell comprises of
    multiple states from a list of predefined `TileImage`.
    """
    __slots__ = '_collapsed', '_options'
    def __init__(self, patterns: Iterable[TileImage]):
        """
        Initialize an uncollapse cells from a list of `TileImage`.

        :param Iterable[TileImage] patterns: A list of predefined tiles.
            Each tile carries along an information on what other tiles it
            can be adjacent to.
        """
        self._options = list(patterns)
        self._collapsed = False

        if not len(self._options):
            raise ValueError('patterns is empty...')

    @property
    def entropy(self) -> float:
        r"""
        Calculate the entropy of the current cell.
        When all tiles of a cell have the same probability of collapsing,
        uncollapsed cells with more states have higher entropy than those
        with less states. For cells that have been collapsed, its entropy is 0.

        For details, the entropy is calculated using the Shannon-entropy formula:

        .. math::

            \text{entropy} = \log_2(\sum_{i=0}^{n-1}\text{freq}_i)
                - \sum_{i=0}^{n-1}\text{freq}_i\log_2(\text{freq}_i)
        
        where :math:`n` is the number of possible states for a cell and
        :math:`\text{freq}_i` is the frequency of the *i*-th state.

        :return: The entropy duh.
        :rtype: float
        """
        if self._collapsed: return 0
        elif not len(self._options): return np.inf

        total = sum(tile.frequency for tile in self._options)
        return (
            np.log2(total) -
            sum(tile.frequency * np.log2(tile.frequency) for tile in self._options) / total
        )
    
    @property
    def image(self) -> Optional[NDArray]:
        """
        Image representation of the current cell. In the case
        the cell has collapsed, this is the image of the tile it has
        collapsed to. In the case the cell is uncollapsed, this will be
        a image where the pixel values are averaged across all states.

        Note: Invalid cell will not have an image representation
        """
        if not len(self._options): return None
        if self._collapsed: return self._options[0].image
        else:
            image = np.array([tile.image for tile in self._options])
            # image = image.mean(axis=0)
            image[:] = image.mean(axis=0).mean(axis=(0, 1))
            return image.astype('uint8')
    
    @property
    def is_collapsed(self) -> bool: return self._collapsed
    
    @property
    def is_valid(self) -> bool:
        """
        Whether or not this is a valid cell. All cells start out as valid
        (having states to collapse) and may end up being invalid (having
        no state to collapse to) because of the constraints enforce by
        adjacent cells.
        """
        return bool(len(self._options))

    def update_options(self,
        cell_image: 'Cell',
        direction: Direction
    ) -> bool:
        """
        Update the options for a cell based on adjacent cells. This will
        essentially remove options that can not be adjacent to the given
        cell.

        :param Cell cell_image: The adjacent cell.
        :param Direction direction: The position of this cell
            relative to the `cell_image`.

        :return bool: Whether or not the options has changed after updating.
        """
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
        """
        Collapse the current cell. This will randomly pick an option
        from the available options.
        """
        counts = [tile.frequency for tile in self._options]
        self._options = rand.sample(self._options, 1, counts=counts)
        self._collapsed = True