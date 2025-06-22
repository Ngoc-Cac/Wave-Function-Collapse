import numpy as np


from .algos import _wfc
from .cell_image import TileImage


from numpy.typing import NDArray
from typing import (
    Generator,
    Iterable
)


class CollapsedError(Exception):
    """
    Exception thrown when WFC has already collapsed for the current configuration
    """

class WFC:
    __slots__ = (
        '_generator',
        '_need_update',
        '_output_dim',
        '_patterns',
        '_repeat_til_success',
        '_rerun',
        '_return_val'
    )
    def __init__(self,
        output_dimension: tuple[int, int],
        patterns: Iterable[TileImage],
        *,
        repeat_until_success: bool = True,
        rerun: bool = True
    ):
        self._need_update = True
        self._return_val = None

        self.output_dimension = output_dimension
        self.patterns = patterns
        self.repeat_until_success = repeat_until_success
        self.rerun = rerun

    @property
    def output_dimension(self) -> tuple[int, int]:
        """
        The dimension (in tiles) of the output grid. For example,
        the dimension (2, 2) will output a grid of 2 tiles wide
        and 2 tiles high. The dimension in pixels depends on the image
        representation of the tiles.
        """
        return self._output_dim
    @output_dimension.setter
    def output_dimension(self, new_dim: tuple[int, int]):
        if (
            not isinstance(new_dim, tuple) or
            len(new_dim) != 2 or
            any((not isinstance(i, int)) for i in new_dim)
        ):
            raise TypeError(f"Expected a tuple of two int: {new_dim}")
        elif any((dim < 1) for dim in new_dim):
            raise ValueError("Dimension must be larger than 0")
        self._output_dim = new_dim
        self._need_update = True

    @property
    def patterns(self) -> Iterable[TileImage]:
        """
        The current set of tiles to do wave function collapse on.
        """
        return iter(self._patterns)
    @patterns.setter
    def patterns(self, new_patterns: Iterable[TileImage]):
        if any((not isinstance(tile, TileImage) for tile in new_patterns)):
            raise TypeError("Expected an Iterable of TileImage")
        self._patterns = list(new_patterns)
        self._need_update = True

    @property
    def repeat_until_success(self) -> bool:
        """
        Whether to do wave function collapse until all cells are
        collapsed. During a collapse, if a cell becomes invalid, the
        algoirthm will reset to a new grid and run again.
        """
        return self._repeat_til_success
    @repeat_until_success.setter
    def repeat_until_success(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError('repeat value must be a bool')
        self._repeat_til_success = value
        self._need_update = True

    @property
    def rerun(self) -> bool:
        """
        Whether or not to rerun the wave function collapse algorithm
        once the current state has been collapsed. This is different
        to `repeat_until_success` in the sense that the algorithm is not run
        again if the all cells have been collapsed to preserve the result.

        If `rerun` is True, calling `run()` will run the algorithm again and
        overwrite the wfc_result in the previous run.
        """
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
        """
        The result of the wave function collapse. If the current grid has
        been collapsed, this will return the collapsed result. Otherwise,
        this will return a grid of cells where each cell is represented by a
        superposition of all available states.

        :return: A tuple of bool and numpy.NDArray. The bool represents whether
            or not all cells have been collapsed. The numpy.NDArray is the image
            representation of the grid.
        :rtype: tuple[bool, numpy.NDArray]
        """
        if self._return_val is None:
            image = NDArray(self._patterns[0].image.shape)
            image[:] = np.mean(np.mean([tile.image for tile in self._patterns], axis=0), axis=(0, 1))
            return False, image.astype('uint8')
        else:
            return self._return_val


    def _init_gen(self):
        """
        Initialize a wave function collapse generator.
        """
        self._generator = _wfc(
            self._patterns,
            self._output_dim,
            self._repeat_til_success
        )
        self._return_val = None
        self._need_update = False


    def run(self) -> tuple[bool, NDArray]:
        """
        Run the wave function collapse algorithm on the current configuration.
        Internally, this will just iterate over the current object to get the final
        result.
        
        If `rerun` is False and all cells have been collapsed. This will raise a
        CollapsedError to avoid overwriting the current result.

        :return: A tuple of bool and numpy.NDArray. The bool represents whether
            or not all cells have been collapsed. The numpy.NDArray is the image
            representation of the grid.
        :rtype: tuple[bool, numpy.NDArray]
        """
        if self._need_update: self._init_gen()
        prev_result = self._return_val
        for _ in self: pass
        
        if self._return_val is None:
            self._return_val = prev_result
            err_msg = (
                "The current configuration for Wave Function Collapse has already"
                " been collapsed. Consider setting rerun = True to rerun. If you"
                " want to just get the previous result of the WFC, use 'wfc_result'"
                " attribute instead."
            )
            raise CollapsedError(err_msg)
        return self._return_val


    def __iter__(self
    ) -> Generator[NDArray, None, tuple[bool, NDArray]]:
        return self
    
    def __next__(self) -> NDArray:
        if self._need_update: self._init_gen()
        try:
            return next(self._generator)
        except StopIteration as exc:
            self._return_val = exc.value
            if self._rerun: self._need_update = True
            raise exc