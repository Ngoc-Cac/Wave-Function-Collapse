from PyQt6.QtCore import (
    Qt,
    pyqtSignal
)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
    QVBoxLayout
)

from GUI.dialogs import ErrorDialog
from GUI.drawing_widgets import MplCanvas

from typing import Literal, Optional


INFO_FONT = QFont()
INFO_FONT.setPointSize(10)

class Home(QWidget):
    button_clicked=pyqtSignal(str)
    change_dim_req=pyqtSignal(int, int)
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()
        vbox.addLayout(self._init_buttons())
        vbox.addWidget(self._init_canvas())
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.start_butt.setFont(INFO_FONT)
        self.pause_butt.setFont(INFO_FONT)
        self.start_butt.setFixedWidth(50)
        self.pause_butt.setFixedWidth(50)
        self.start_butt.clicked.connect(lambda: self.button_clicks('start'))
        self.pause_butt.clicked.connect(lambda: self.button_clicks('pause'))

        dim_butt = QPushButton()
        dim_butt.setText('Change dimension')
        dim_butt.setFont(INFO_FONT)
        dim_butt.setFixedWidth(130)
        dim_butt.clicked.connect(lambda: self.button_clicks('dim'))

        self.line_edit = QLineEdit()
        self.line_edit.setFont(INFO_FONT)
        self.line_edit.setFixedWidth(100)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(dim_butt)
        hbox2.addWidget(self.line_edit)

        grid = QGridLayout()
        grid.addWidget(self.start_butt, 1, 0)
        grid.addWidget(self.pause_butt, 1, 1)
        grid.addLayout(hbox2, 0, 0, 1, 2)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return grid
    
    def button_clicks(self, button_type: Literal['start', 'pause', 'dim']):
        if button_type == 'start':
            self.start_butt.setDisabled(True)
            self.button_clicked.emit('start')
        elif button_type == 'pause':
            self.start_butt.setEnabled(False)
            self.button_clicked.emit('pause')
        elif button_type == 'dim':
            processed_ints = self._process_text()
            if not processed_ints is None: self.change_dim_req.emit(*processed_ints)

    def _process_text(self) -> Optional[tuple[int, int]]:
        user_in = self.line_edit.text()

        if (
            (len(nums := user_in.split(',')) != 2) or\
            (not nums[0]) or\
            (not nums[1])
        ):
            ErrorDialog(self, 'Dimension input should be of format (rows, cols)!').exec()
            return
        
        if nums[0][0] == '(':
            nums[0] = nums[0][1:]
        if (len(nums[1]) > 1) and nums[1][-1] == ')':
            nums[1] = nums[1][:-1]

        try: rows, cols = int(nums[0]), int(nums[1])
        except ValueError:
            ErrorDialog(self, 'Found non-numeric character. Please recheck input!').exec()
            return

        self.line_edit.clear()
        return rows, cols