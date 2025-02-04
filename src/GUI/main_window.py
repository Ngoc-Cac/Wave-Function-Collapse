import os.path as osp

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QMainWindow

from GUI import _ROOT_DIR
from GUI.home import Home
from GUI.drawing_widgets import Animator

from utilities.utils import load_patterns
from wfc.cell_image import TileImage
from wfc.wfc import WFC

from typing import Literal


_tile_folder = osp.join(_ROOT_DIR, 'images')
_default_tiles = [TileImage(pattern, 1) for pattern in load_patterns(osp.join(_tile_folder, 'tilesets', 'Circuit'))]
_dimension = (10, 30)
_WFC = WFC(_dimension, _default_tiles, rerun=True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1100, 650)

        self.home = Home()
        self.setCentralWidget(self.home)

        self.threadpool = QThreadPool()
        self.animator = Animator(self.home.canvas, _WFC, 50)
        self.animator.finished.connect(lambda: self.process_animation('finish'))

        self.home.start_butt.clicked.connect(lambda: self.process_animation('start'))
        self.home.pause_butt.clicked.connect(lambda: self.process_animation('pause'))

    def process_animation(self, state: Literal['start', 'pause', 'finish']):
        match state:
            case 'start':
                self.home.start_butt.setDisabled(True)
                self.threadpool.start(self.animator)
            case 'pause':
                self.home.start_butt.setDisabled(False)
                self.animator.terminate()
            case 'finish':
                self.home.start_butt.setDisabled(False)