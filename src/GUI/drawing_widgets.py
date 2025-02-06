import time

import matplotlib
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtCore import (
    QObject,
    QRunnable,
    pyqtSignal,
    pyqtSlot
)

from wfc.wfc import WFC
from utilities.utils import show_tiles

from typing import TypeAlias

ms: TypeAlias = int

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, width=8, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.invert_yaxis()
        self.ax.axis('off')
        super().__init__(self.fig)

    def show_image(self, image):
        self.ax.clear()
        axes_image = self.ax.imshow(image)
        self.fig.tight_layout()
        return axes_image, self.ax
    
    def show_tiles(self, tiles):
        self.ax.clear()
        show_tiles(tiles, ax=self.ax)
        self.fig.tight_layout()


class _AnimatorSignals(QObject):
    finished=pyqtSignal()

class Animator(QRunnable):
    def __init__(self, canvas: MplCanvas, wfc: WFC, interval: ms):
        super().__init__()
        self._canvas = canvas
        self._wfc = wfc
        self._sleep_int = interval
        self._signal = _AnimatorSignals()
        self._kill = False

        self.setAutoDelete(False)

    @pyqtSlot()
    def run(self):
        self._kill = False
        axes_image = None
        try: image = next(self._wfc)
        except StopIteration:
            image = self._wfc.wfc_result[1]
            self._about_to_finish()

        while not self._kill:
            if axes_image is None:
                axes_image, ax = self._canvas.show_image(image)
                self._canvas.draw()
            else:
                axes_image.set_data(image)
                ax.draw_artist(axes_image)
                self._canvas.blit(ax.bbox)

            if self._sleep_int > 0: time.sleep(self._sleep_int / 1000)

            try: image = next(self._wfc)
            except StopIteration:
                image = self._wfc.wfc_result[1]
                self._about_to_finish()


    @property
    def finished(self):
        return self._signal.finished
    
    @property
    def is_running(self):
        return not self._kill
    
    def _about_to_finish(self):
        self._kill = True
        self._signal.finished.emit()

    def terminate(self):
        self._kill = True