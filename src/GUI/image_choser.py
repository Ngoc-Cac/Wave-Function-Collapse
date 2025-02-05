from matplotlib.pyplot import imread

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from GUI.drawing_widgets import MplCanvas
from utilities.utils import load_patterns, generate_patterns

class ImageLoader(QWidget):
    load_pattern_req=pyqtSignal(str, bool)
    def __init__(self):
        super().__init__()

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

        vbox = QVBoxLayout()
        vbox.addWidget(generate_pattern)

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
        placeholder_widget.setFixedSize(400, 400)

        temp2 = QVBoxLayout()
        temp2.addWidget(self.pattern_canvas)
        placeholder_widget2 = QWidget()
        placeholder_widget2.setLayout(temp2)
        placeholder_widget2.setFixedSize(400, 400)

        return placeholder_widget, placeholder_widget2
    
    def browse(self, file: bool):
        if file:
            path = QFileDialog.getOpenFileName(self, 'Choose An Image', None, 'PNG Files (*.png)')
            patterns = generate_patterns(path)

            self.canvas.show_image(imread(path[0]))
            self.pattern_canvas.show_tiles(patterns)
            self.canvas.draw()
            self.pattern_canvas.draw()
        else:
            path = QFileDialog.getExistingDirectory(self, 'Choose A Tileset')
            patterns = load_patterns(path)

            self.pattern_canvas.show_tiles(patterns)
            self.pattern_canvas.draw()

    def generate_patterns(self):
        pass