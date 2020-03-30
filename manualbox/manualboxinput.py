from PyQt5 import QtGui, QtWidgets, QtCore


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os


from .utils import get_asset_path


class MainInput(QtWidgets.QDialog):
    CSS = """
            QLabel#filepath {
                color: black;
                font-size: 20px;
                background-color: rgb(255,255,255);
            }
            QLabel#processname {
                background-color: rgb(255,255,255);
            }
            QLabel {
                background-color: rgb(255,255,255);
                color: rgb(0,0,0);
            }

            QPushButton {
                background-color: rgb(255,255,255);
            }
            QWidget {
                background-color: rgb(255,255,255);
            }

    """

    def __init__(self, parent=None, display_path="", process_name=""):
        super(MainInput, self).__init__(parent)
        self.setModal(True)
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
        if process_name:
            process_txt = f'The process <span style="color:#aa0000">{process_name}</span> is asking to access:'
            process_label = QLabel()
            process_label.setTextFormat(Qt.RichText)
            process_label.setText(process_txt)
            process_label.setObjectName("processname")
            self.layout.addWidget(process_label)

        label = QLabel(display_path)
        label.setObjectName("filepath")
        self.layout.addWidget(label)
        self.buttonLayout = QHBoxLayout()
        self.okay = QPushButton(QIcon(QPixmap(get_asset_path("check.png"))), "Allow")
        self.cancel = QPushButton(QIcon(QPixmap(get_asset_path("cross.png"))), "Deny")
        self.buttonLayout.addWidget(self.okay)
        self.buttonLayout.addWidget(self.cancel)
        buttons = QWidget()
        buttons.setLayout(self.buttonLayout)
        self.layout.addWidget(buttons)
        self.okay.clicked.connect(self.okayCalled)
        self.cancel.clicked.connect(self.cancelCalled)
        # self.widget = QWidget()
        # self.widget.setLayout(self.layout)
        self.setLayout(self.layout)
        # self.setCentralWidget(self.widget)
        self.setStyleSheet(self.CSS)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        screen_size = QDesktopWidget().screenGeometry()
        window_size = self.geometry()
        x_center = (screen_size.width() - window_size.width()) / 2
        y_center = (screen_size.height() - window_size.height()) / 2
        self.move(x_center, y_center)
        self.setWindowTitle("Will you allow access of the following file?")
        self.userstatus = ""

    def okayCalled(self):
        self.userstatus = "okay"
        self.hide()

    def cancelCalled(self):
        self.userstatus = "nope"
        self.hide()


def main(display_path="", process_name=""):
    form = MainInput(display_path=display_path, process_name=process_name)
    form.show()
    form.setWindowState(Qt.WindowState.WindowActive)
    form.raise_()
    form.exec()
    while not form.isHidden():
        pass
    return form.userstatus


if __name__ == "__main__":
    if len(sys.argv) == 3:
        app = QtWidgets.QApplication(sys.argv)
        main(sys.argv[1], sys.argv[2])
