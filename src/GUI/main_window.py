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

from wfc.cell_image import TileImage
from wfc.utils import load_patterns
from wfc.wfc import WFC

from typing import Literal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setFixedSize(1280, 720)
        self.setFixedSize(1152, 648)
        self.setWindowTitle('Wave Function Collapse Demo')

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
        self.home.change_dim_req.connect(lambda rows, cols: self.config_wfc((rows, cols), 'dim'))
        self.animator.finished.connect(lambda: self.process_animation('finish'))
        self.tab.currentChanged.connect(self._change_tab)
        self.image_loader.change_pattern_req.connect(lambda x: self.config_wfc(x, 'patterns'))

    def _change_tab(self, index: int):
        self.home.start_butt.setDisabled(False)
        self.process_animation('pause')

    def _prepare_wfc(self):
        path = osp.join(_ROOT_DIR, 'images', 'tilesets', 'Circuit')
        default_tiles = [TileImage(pattern, 1) for pattern in load_patterns(path)]
        dimension = (20, 30)
        self.WFC = WFC(dimension, default_tiles, rerun=True)
        self.home.canvas.show_image(self.WFC.wfc_result[1])
        self.home.canvas.draw()
        self.home.dim_label.setText(f'Dimension: {dimension}')

        self.threadpool = QThreadPool()
        self.animator = Animator(self.home.canvas, self.WFC, 2)


    def config_wfc(self, value, param: Literal['patterns', 'dim']):
        if param == 'patterns':
            try:
                self.WFC.patterns = value
                ConfirmationDialog(self, 'Successfully saved patterns!').exec()
            except TypeError:
                ErrorDialog(self, 'Found non-tile data while saving patterns!').exec()
                return
        elif param == 'dim':
            try:
                self.WFC.output_dimension = value
                self.home.dim_label.setText(f'Dimension: {value}')
                ConfirmationDialog(self, f'Succesfully set dimension to {value}').exec()
            except TypeError:
                ErrorDialog(self, 'Something went wrong while setting new dimension').exec()
                return
            

        _, ax = self.home.canvas.show_image(self.WFC.wfc_result[1])
        self.home.canvas.draw()
        self.home.canvas.blit(ax.bbox)


    def process_animation(self, state: Literal['start', 'pause', 'finish']):
        match state:
            case 'start':
                self.threadpool.start(self.animator)
            case 'pause':
                if self.animator.is_running:
                    self.animator.terminate()
            case 'finish':
                self.home.start_butt.setDisabled(False)