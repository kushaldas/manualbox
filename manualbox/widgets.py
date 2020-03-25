from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore

import os
from pathlib import Path


class MountEdit(QWidget):
    """
    Widget to store selected Directory for mount path
    """

    def __init__(self):
        super().__init__()

        # Set layout
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.mountpathTxt = QLineEdit()
        self.selectMountPathButton = QPushButton("...")
        self.selectMountPathButton.setToolTip("Select a mount path")
        self.selectMountPathButton.clicked.connect(self.selectMountPath)
        self.home = str(Path.home())
        layout.addWidget(self.mountpathTxt)
        layout.addWidget(self.selectMountPathButton)
        layout.setContentsMargins(0, 0, 0, 0)

    def selectMountPath(self):
        dirpath = QFileDialog.getExistingDirectory(
            self,
            "Select empty directory as mount path",
            os.path.join(self.home, "secured"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        self.mountpathTxt.setText(dirpath)

    def text(self):
        return self.mountpathTxt.text()

    def setText(self, text):
        self.mountpathTxt.setText(text)
