import os.path as osp

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget
)

from GUI import _ROOT_DIR
from GUI.dialogs import ErrorDialog, ConfirmationDialog
from GUI.drawing_widgets import Animator
from GUI.home import Home
from GUI.image_choser import ImageLoader

from utilities.utils import load_patterns
from wfc.cell_image import TileImage
from wfc.wfc import WFC

from typing import Literal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setFixedSize(1280, 720)
        self.setFixedSize(1152, 648)

        self.home = Home()
        self.image_loader = ImageLoader()

        self.tab = QTabWidget()
        self.tab.addTab(self.home, 'Home')
        self.tab.addTab(self.image_loader, 'Load Image')

        self.setCentralWidget(self.tab)


        self._prepare_wfc()
        self._establish_connections()


    def _establish_connections(self):
        self.home.button_clicked.connect(self.process_animation)
        self.animator.finished.connect(lambda: self.process_animation('finish'))
        self.tab.currentChanged.connect(lambda _: self.process_animation('pause'))
        self.image_loader.change_pattern_req.connect(lambda x: self.config_wfc(x, 'patterns'))

    def _prepare_wfc(self):
        path = osp.join(_ROOT_DIR, 'images', 'tilesets', 'Circuit')
        default_tiles = [TileImage(pattern, 1) for pattern in load_patterns(path)]
        dimension = (10, 30)
        self.WFC = WFC(dimension, default_tiles, rerun=True)
        self.home.canvas.show_image(self.WFC.wfc_result[1])
        self.home.canvas.draw()

        self.threadpool = QThreadPool()
        self.animator = Animator(self.home.canvas, self.WFC, 10)


    def config_wfc(self, value, param: Literal['patterns', 'dim']):
        if param == 'patterns':
            try:
                self.WFC.patterns = value
            except TypeError:
                ErrorDialog(self, 'Found non-tile data while saving patterns!').show()
                return

        self.home.canvas.show_image(self.WFC.wfc_result[1])
        self.home.canvas.draw()

    def process_animation(self, state: Literal['start', 'pause', 'finish']):
        match state:
            case 'start':
                self.threadpool.start(self.animator)
            case 'pause':
                if self.animator.is_running:
                    self.animator.terminate()
            case 'finish':
                self.home.start_butt.setDisabled(False)