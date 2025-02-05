from matplotlib.pyplot import imread

from PyQt6.QtGui import QFont
from PyQt6.QtCore import (
    Qt,
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget
)

from GUI.dialogs import WarningDialog
from GUI.drawing_widgets import MplCanvas
from utilities.utils import load_patterns, generate_patterns
from wfc.cell_image import TileImage

from typing import Literal


INFO_FONT = QFont()
INFO_FONT.setPointSize(11)
INFO_FONT.setBold(True)
ALTER_INFO_FONT = QFont()
ALTER_INFO_FONT.setPointSize(10)

class _ButtonPanel(QWidget):
    browse_req=pyqtSignal(bool)
    change_config_req=pyqtSignal(int, str)
    generate_req=pyqtSignal()
    save_req=pyqtSignal(bool)
    def __init__(self):
        super().__init__()

        grid = QGridLayout()

        image, tileset = self._init_browse_area()
        grid.addWidget(image, 0, 0)
        grid.addWidget(tileset, 0, 1)

        generate, save = self._init_pattern_area()
        grid.addWidget(generate, 1, 0)
        grid.addWidget(save, 1, 1)

        rotate, pix_hbox = self._init_config_area()
        grid.addWidget(rotate, 2, 0)
        grid.addLayout(pix_hbox, 2, 1)

        self.setLayout(grid)

    def _init_browse_area(self) -> tuple[QPushButton, QPushButton]:
        choose_image = QPushButton()
        choose_tileset = QPushButton()
        choose_image.setText('Choose Image...')
        choose_tileset.setText('Choose Tileset...')
        choose_image.setFont(INFO_FONT)
        choose_tileset.setFont(INFO_FONT)
        choose_image.setFixedSize(150, 30)
        choose_tileset.setFixedSize(135, 30)
        choose_image.clicked.connect(lambda: self.browse_req.emit(True))
        choose_tileset.clicked.connect(lambda: self.browse_req.emit(False))

        return choose_image, choose_tileset
    
    def _init_pattern_area(self) -> tuple[QPushButton, QPushButton]:
        generate_pattern = QPushButton()
        save_pattern = QPushButton()
        generate_pattern.setText('Generate Patterns')
        save_pattern.setText('Save Patterns')
        
        generate_pattern.setFont(INFO_FONT)
        save_pattern.setFont(INFO_FONT)
        generate_pattern.setFixedSize(150, 30)
        save_pattern.setFixedSize(135, 30)
        
        generate_pattern.clicked.connect(self.generate_req.emit)
        save_pattern.clicked.connect(self.save_req.emit)
        
        return generate_pattern, save_pattern

    def _init_config_area(self) -> tuple[QPushButton, QHBoxLayout]:
        rotate_check = QCheckBox()
        rotate_check.setText('Rotate patterns')
        rotate_check.setChecked(False)
        rotate_check.setFont(INFO_FONT)
        rotate_check.stateChanged.connect(lambda num: self.change_config_req.emit(num, 'rotate'))

        npix_spin = QSpinBox()
        npix_spin.setRange(1, 10)
        npix_spin.setSuffix(' pixels')
        npix_spin.lineEdit().setReadOnly(True)
        npix_spin.setValue(3)
        npix_spin.setFont(ALTER_INFO_FONT)
        npix_spin.valueChanged.connect(lambda num: self.change_config_req.emit(num, 'n_pixels'))

        info_label = QLabel('No. of pixels: ')
        info_label.setFont(INFO_FONT)

        hbox = QHBoxLayout()
        hbox.addWidget(info_label)
        hbox.addWidget(npix_spin)
        hbox.setAlignment(Qt.AlignmentFlag.AlignRight)

        return rotate_check, hbox


class ImageLoader(QWidget):
    change_pattern_req=pyqtSignal(list)
    def __init__(self):
        super().__init__()

        self._patterns_data = {'patterns': [],
                               'rotate': False,
                               'n_pixels': 3,
                               'path': (True, '')}
        place1, place2 = self._init_canvas()

        grid = QGridLayout()
        grid.addWidget(self._init_button_panel(), 0, 0)
        grid.addWidget(place1, 0, 1)
        grid.addWidget(place2, 0, 2)
        self.setLayout(grid)

    def _init_button_panel(self):
        panel = _ButtonPanel()
        panel.setFixedSize(390, 115)
        panel.browse_req.connect(self.browse)
        panel.generate_req.connect(self.generate_patterns)
        panel.save_req.connect(lambda: self.change_pattern_req.emit(self._patterns_data['patterns']))
        panel.change_config_req.connect(self.change_config)
        return panel

    def _init_canvas(self):
        self.canvas = MplCanvas(5, 5)
        self.pattern_canvas = MplCanvas(5, 5)
        self.canvas.figure.suptitle('Loaded Image')
        self.pattern_canvas.figure.suptitle('List of Patterns')

        temp = QVBoxLayout()
        temp.addWidget(self.canvas)
        placeholder_widget = QWidget()
        placeholder_widget.setLayout(temp)
        placeholder_widget.setFixedSize(381, 381)

        temp2 = QVBoxLayout()
        temp2.addWidget(self.pattern_canvas)
        placeholder_widget2 = QWidget()
        placeholder_widget2.setLayout(temp2)
        placeholder_widget2.setFixedSize(381, 381)

        return placeholder_widget, placeholder_widget2
    
    def change_config(self, value: int, param: Literal['rotate', 'n_pixels']):
        if param == 'rotate': value = (value == 2)
        # elif param == 'n_pixels' and value > 3:
        self._patterns_data[param] = value

    def browse(self, file: bool):
        if file:
            path = QFileDialog.getOpenFileName(self, 'Choose An Image', None, 'PNG Files (*.png)')
            path = path[0]
            self.canvas.show_image(imread(path))
            self.canvas.draw()
        else:
            path = QFileDialog.getExistingDirectory(self, 'Choose A Tileset')

        if not path: return

        self._patterns_data['path'] = (file, path)

        self.generate_patterns()

    def generate_patterns(self):
        path, rotate = self._patterns_data['path'][1], self._patterns_data['rotate']
        if self._patterns_data['path'][0]:
            self._patterns_data['patterns'] = generate_patterns(path, self._patterns_data['n_pixels'],
                                                                rotate)
        else:
            self._patterns_data['patterns'] = [TileImage(tile, 1) for tile in load_patterns(path, rotate)]

        self.pattern_canvas.show_tiles([i.image for i in self._patterns_data['patterns']])
        self.pattern_canvas.draw()