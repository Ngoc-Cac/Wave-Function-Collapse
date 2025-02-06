from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QStyle,
    QVBoxLayout
)


class ErrorDialog(QDialog):
    def __init__(self, parent, error_msg):
        super().__init__(parent)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.close)
        message = QLabel(error_msg)

        vbox = QVBoxLayout()
        vbox.addWidget(message)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.setWindowTitle('Something very wrong happened :(')
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
        self.setWindowIcon(icon)

class ConfirmationDialog(QDialog):
    def __init__(self, parent, msg):
        super().__init__(parent)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.close)
        message = QLabel(msg)

        vbox = QVBoxLayout()
        vbox.addWidget(message)
        vbox.addWidget(self.buttonBox)
        self.setLayout(vbox)

        self.setWindowTitle('Just passing along some news here :)')
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        self.setWindowIcon(icon)