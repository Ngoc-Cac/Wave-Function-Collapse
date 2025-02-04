import os.path as osp

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

        self.canvas = MplCanvas()
        
        vbox = QVBoxLayout()
        vbox.addLayout(self._init_buttons())
        vbox.addWidget(self.canvas)
        self.setLayout(vbox)

    def _init_buttons(self) -> QHBoxLayout:
        self.start_butt = QPushButton()
        self.pause_butt = QPushButton()
        self.start_butt.setText('Start')
        self.pause_butt.setText('Pause')
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.start_butt)
        hbox.addWidget(self.pause_butt)
        return hbox