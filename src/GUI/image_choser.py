from matplotlib.pyplot import imread

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

from GUI.drawing_widgets import MplCanvas
from utilities.utils import load_patterns, generate_patterns

from typing import Literal


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
        grid.addLayout(self._init_browser(), 0, 0)
        grid.addLayout(self._init_config(), 1, 0)
        grid.addWidget(place1, 0, 1)
        grid.addWidget(place2, 1, 1)
        self.setLayout(grid)

    def _init_browser(self):
        choose_image = QPushButton()
        choose_tileset = QPushButton()
        choose_image.setText('Choose Image...')
        choose_tileset.setText('Choose Tileset...')
        choose_image.clicked.connect(lambda: self.browse(True))
        choose_tileset.clicked.connect(lambda: self.browse(False))

        hbox = QHBoxLayout()
        hbox.addWidget(choose_image)
        hbox.addWidget(choose_tileset)
        return hbox
    
    def _init_config(self):
        generate_pattern = QPushButton()
        generate_pattern.setText('Generate Patterns')
        generate_pattern.clicked.connect(self.generate_patterns)
        save_pattern = QPushButton()
        save_pattern.setText('Save Patterns')
        save_pattern.clicked.connect(lambda: self.change_pattern_req.emit(self._patterns_data['patterns']))

        hbox1 = QHBoxLayout()
        hbox1.addWidget(generate_pattern)
        hbox1.addWidget(save_pattern)

        rotate_check = QCheckBox()
        rotate_check.setText('Rotate patterns')
        rotate_check.setChecked(False)
        rotate_check.stateChanged.connect(lambda num: self.change_config(num, 'rotate'))

        npix_spin = QSpinBox()
        npix_spin.setRange(1, 10)
        npix_spin.setSuffix(' pixels')
        npix_spin.lineEdit().setReadOnly(True)
        npix_spin.setValue(3)
        npix_spin.valueChanged.connect(lambda num: self.change_config(num, 'n_pixels'))

        info_label = QLabel('n pixels (please change)')

        hbox2 = QHBoxLayout()
        hbox2.addWidget(info_label)
        hbox2.addWidget(npix_spin)
        hbox2.setAlignment(Qt.AlignmentFlag.AlignRight)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(rotate_check)
        hbox3.addLayout(hbox2)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox3)
        vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        return vbox

    def _init_canvas(self):
        self.canvas = MplCanvas(5, 5)
        self.pattern_canvas = MplCanvas(5, 5)
        self.canvas.figure.suptitle('Loaded Image')
        self.pattern_canvas.figure.suptitle('List of Patterns')

        temp = QVBoxLayout()
        temp.addWidget(self.canvas)
        placeholder_widget = QWidget()
        placeholder_widget.setLayout(temp)
        placeholder_widget.setFixedSize(321, 321)

        temp2 = QVBoxLayout()
        temp2.addWidget(self.pattern_canvas)
        placeholder_widget2 = QWidget()
        placeholder_widget2.setLayout(temp2)
        placeholder_widget2.setFixedSize(321, 321)

        return placeholder_widget, placeholder_widget2
    
    def change_config(self, value: int, param: Literal['rotate', 'n_pixels']):
        if param == 'rotate': value = (value == 2)
        self._patterns_data[param] = value

    def browse(self, file: bool):
        if file:
            path = QFileDialog.getOpenFileName(self, 'Choose An Image', None, 'PNG Files (*.png)')
            self.canvas.show_image(imread(path[0]))
            self.canvas.draw()
        else:
            path = QFileDialog.getExistingDirectory(self, 'Choose A Tileset')

        self._patterns_data['path'] = (file, path)
        self.generate_patterns()

    def generate_patterns(self):
        path, rotate = self._patterns_data['path'][1], self._patterns_data['rotate']
        if self._patterns_data['path'][0]:
            self._patterns_data['patterns'] = generate_patterns(path, self._patterns_data['n_pixels'],
                                                                rotate)
        else:
            self._patterns_data['patterns'] = load_patterns(path, rotate)

        self.pattern_canvas.show_tiles(self._patterns_data['patterns'])
        self.pattern_canvas.draw()