from PyQt5 import QtGui, QtWidgets, QtCore


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(file_name):
    "Return the absolute path for requested asset"
    return os.path.join(BASE_PATH, "assets", file_name)


class MainWindow(QtWidgets.QMainWindow):
    CSS = """
            QLabel#filepath {
                color: black;
                font-size: 25px;
                background-color: rgb(255,255,255);
            }
            QLabel {
                background-color: rgb(255,255,255);
            }

            QPushButton {
                background-color: rgb(255,255,255);
            }
            QWidget {
                background-color: rgb(255,255,255);
            }

    """

    def __init__(
        self, parent=None,
    ):
        super(MainWindow, self).__init__(parent)
        self.layout = QVBoxLayout()
        iconlayout = QHBoxLayout()
        iconlabel = QLabel(pixmap=QPixmap(get_asset_path("mainicon.png")))
        iconlayout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum,)
        )
        iconlayout.addWidget(iconlabel)
        iconlayout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum,)
        )
        iconlayoutWidget = QWidget()
        iconlayoutWidget.setLayout(iconlayout)

        self.layout.addWidget(iconlayoutWidget)
        label = QLabel(sys.argv[1])
        label.setObjectName("filepath")
        self.layout.addWidget(label)
        self.buttonLayout = QHBoxLayout()
        self.okay = QPushButton("Allow")
        self.cancel = QPushButton("Cancel")
        self.buttonLayout.addWidget(self.okay)
        self.buttonLayout.addWidget(self.cancel)
        buttons = QWidget()
        buttons.setLayout(self.buttonLayout)
        self.layout.addWidget(buttons)
        self.okay.clicked.connect(self.okayCalled)
        self.cancel.clicked.connect(self.cancelCalled)
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setStyleSheet(self.CSS)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        screen_size = QDesktopWidget().screenGeometry()
        window_size = self.geometry()
        x_center = (screen_size.width() - window_size.width()) / 2
        y_center = (screen_size.height() - window_size.height()) / 2
        self.move(x_center, y_center)
        self.setWindowTitle("Will you allow access of the following file?")

    def okayCalled(self):
        print("okay")
        sys.exit(0)

    def cancelCalled(self):
        print("nope")
        sys.exit(-1)


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()