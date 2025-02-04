from PyQt6.QtWidgets import QApplication

from GUI.main_window import MainWindow

app = QApplication([])
root = MainWindow()

app.aboutToQuit.connect(root.animator.terminate)

root.show()
app.exec()