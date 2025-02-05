import os.path as osp

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
    QVBoxLayout
)

from GUI.drawing_widgets import MplCanvas


class Home(QWidget):
    def __init__(self):
        super().__init__()        
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addLayout(self._init_buttons())
        vbox.addWidget(self._init_canvas())
        self.setLayout(vbox)

    def _init_canvas(self):
        self.canvas = MplCanvas()

        temp = QVBoxLayout()
        temp.addWidget(self.canvas)
        placeholder_widget = QWidget()
        placeholder_widget.setLayout(temp)
        placeholder_widget.setFixedSize(891, 527)

        return placeholder_widget

    def _init_buttons(self) -> QHBoxLayout:
        self.start_butt = QPushButton()
        self.pause_butt = QPushButton()
        self.start_butt.setText('Start')
        self.pause_butt.setText('Pause')
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.start_butt)
        hbox.addWidget(self.pause_butt)
        return hbox