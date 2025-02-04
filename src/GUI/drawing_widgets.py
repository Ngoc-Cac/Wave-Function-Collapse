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

from typing import TypeAlias

ms: TypeAlias = int

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, width=8, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')
        super().__init__(self.fig)


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
        try: image = next(self._wfc)
        except StopIteration:
            image = self._wfc.wfc_result[1]
            self._about_to_finish()
            
        while not self._kill:
            self._canvas.ax.imshow(image)
            self._canvas.draw()
            time.sleep(self._sleep_int / 1000)

            try: image = next(self._wfc)
            except StopIteration:
                image = self._wfc.wfc_result[1]
                self._about_to_finish()


    @property
    def finished(self):
        return self._signal.finished
    
    def _about_to_finish(self):
        self._kill = True
        self._signal.finished.emit()

    def terminate(self):
        self._kill = True