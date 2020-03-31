# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import logging
import subprocess

import os
import sys
import errno
from pathlib import Path
from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
import time as timemodule
from time import time
import argparse
import pickle
import getpass
import platform
import binascii

from pprint import pprint

import psutil
from cryptography.fernet import Fernet, InvalidToken

from . import manualboxinput
from .widgets import MountEdit
from .utils import get_asset_path

try:
    # This is for Debian/Ubuntu
    from fusepy import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context
except ModuleNotFoundError:
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context

    from PyQt5 import QtGui, QtWidgets, QtCore


from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import sys
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


class ManualBoxFS(LoggingMixIn, Operations):
    """
    ManualBoxFS will stay on memory till it is closed.
    """

    error = True

    def __init__(self, key=b"", mountpath="", storagepath="", callback=None):
        self.callback = callback
        self.platform = platform.system()
        self.locker = Fernet(key)
        self.mountpath = mountpath
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 1025
        # The following variable holds if the user granted access or not for a
        # path:fh unique key.
        self.access_records = {}
        now = time()
        self.files["/"] = dict(
            st_mode=(S_IFDIR | 0o755),
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_nlink=2,
            st_uid=os.getuid(),
            st_gid=os.getgid(),
        )
        # This is where we store the encrypted data.
        self.storagepath = storagepath
        if os.path.exists(self.storagepath):
            with open(self.storagepath, "rb") as fobj:
                # This is the encrypted data
                data_from_storage = fobj.read()
                # Now we decrypt
                decrypted_data = self.locker.decrypt(data_from_storage)
                # Now, unpickle
                files, data = pickle.loads(decrypted_data)
                self.files = files
                self.data = data
        self.error = False

    def chmod(self, path, mode):
        self.files[path]["st_mode"] &= 0o770000
        self.files[path]["st_mode"] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]["st_uid"] = uid
        self.files[path]["st_gid"] = gid

    def create(self, path, mode):
        self.files[path] = dict(
            st_mode=(S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=time(),
            st_mtime=time(),
            st_atime=time(),
            st_uid=os.getuid(),
            st_gid=os.getgid(),
        )

        self.fd += 1
        return self.fd

    def flush(self, path, fh):
        return 0

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]

    def getxattr(self, path, name, position=0):
        attrs = self.files[path].get("attrs", {})

        try:
            return attrs[name]
        except KeyError:
            return ""  # Should return ENOATTR

    def listxattr(self, path):
        attrs = self.files[path].get("attrs", {})
        return attrs.keys()

    def mkdir(self, path, mode):
        self.files[path] = dict(
            st_mode=(S_IFDIR | mode),
            st_nlink=2,
            st_size=0,
            st_blocks=12,
            st_ctime=time(),
            st_mtime=time(),
            st_atime=time(),
            st_uid=os.getuid(),
            st_gid=os.getgid(),
        )

        self.files["/"]["st_nlink"] += 1

    def open(self, path, flags):
        self.fd += 1
        if self.fd > 64000:
            self.fd = 1025

        # In Mac, we found that it is doing the open call every time, but not the read call.
        # The following will make sure that the user input happens in that case, but, sadly it
        # also means that user input will be required.
        if self.platform == "Darwin":
            result = self.manualquestion(path, self.fd)
            if not result:
                raise FuseOSError(errno.EIO)
        return self.fd

    def read(self, path, size, offset, fh):
        """
        This method helps to read any file. We intercept this syscall in our project.
        """
        # We need the display with the correct mount path
        if self.platform != "Darwin":
            result = self.manualquestion(path, fh)
            if not result:
                raise FuseOSError(errno.EIO)
        return self.data[path][offset : offset + size]

    def readdir(self, path, fh):
        names = [".", ".."]
        if path != "/":
            for x in self.files:
                if x != "/":
                    if x.startswith(f"{path}/"):
                        name = ""
                        # now we should skip any files/directories one level below
                        length = len(path) + 1
                        if len(x) > length:
                            name = x[length:]
                            if name.find("/") != -1:  # Means another directory
                                continue
                        else:
                            name = x[1:]
                        names.append(name)

        else:
            for x in self.files:
                if x == "/":
                    continue
                if x.count("/") == 1:
                    names.append(x[1:])
        return names

    def readlink(self, path):
        return self.data[path]

    def removexattr(self, path, name):
        attrs = self.files[path].get("attrs", {})

        try:
            del attrs[name]
        except KeyError:
            pass  # Should return ENOATTR

    def rename(self, old, new):
        self.data[new] = self.data.pop(old)
        self.files[new] = self.files.pop(old)

    def rmdir(self, path):
        # with multiple level support, need to raise ENOTEMPTY if contains any files
        self.files.pop(path)
        self.files["/"]["st_nlink"] -= 1

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault("attrs", {})
        attrs[name] = value

    def statfs(self, path):
        """
        We return the stat of the home directory of the user.
        """
        st = os.statvfs(Path.home())
        result = {
            "f_bsize": st.f_bsize,
            "f_frsize": st.f_frsize,
            "f_blocks": st.f_blocks,
            "f_bfree": st.f_bfree,
            "f_bavail": st.f_bavail,
            "f_files": st.f_files,
            "f_ffree": st.f_ffree,
            "f_favail": st.f_favail,
            "f_flag": st.f_flag,
            "f_namemax": st.f_namemax,
        }
        return result

    def symlink(self, target, source):
        self.files[target] = dict(
            st_mode=(S_IFLNK | 0o777), st_nlink=1, st_size=len(source)
        )

        self.data[target] = source

    def truncate(self, path, length, fh=None):
        # make sure extending the file fills in zero bytes
        self.data[path] = self.data[path][:length].ljust(length, "\x00".encode("ascii"))
        self.files[path]["st_size"] = length

    def unlink(self, path):
        self.data.pop(path)
        self.files.pop(path)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]["st_atime"] = atime
        self.files[path]["st_mtime"] = mtime

    def write(self, path, data, offset, fh):
        try:
            self.data[path] = (
                # make sure the data gets inserted at the right offset
                self.data[path][:offset].ljust(offset, "\x00".encode("ascii"))
                + data
                + self.data[path][offset + len(data) :]
                # and only overwrites the bytes that data is replacing
            )
        except Exception as err:
            print(err)
        self.files[path]["st_size"] = len(self.data[path])
        return len(data)

    def __del__(self):
        pass

    def saveondisk(self):
        "We will have to save the Filesystem on disk here."
        # This is incase of an error in decryption of the ~/.manualbox
        if self.error:
            return

        # First dump into pickle
        localdata = pickle.dumps((self.files, self.data))
        # Now, we encrypt
        encrypted = self.locker.encrypt(localdata)

        # Now, write it on the disk
        with open(self.storagepath, "wb") as fobj:
            fobj.write(encrypted)

    def manualquestion(self, path, fh):
        """
        Creates the user input dialog for the given path
        """
        process_name = ""
        logging.debug(f"manualquestion is called for {path} with {fh}")
        display_path = os.path.join(self.mountpath, path[1:])

        # Now let us find the process information
        uid, gid, pid = fuse_get_context()
        try:
            # We don't know if the process is still there or not
            p = psutil.Process(pid=pid)
            process_name = p.name()
        except Exception as err:
            print(err)
            # The process is not there, return now
            return False

        key = f"{path}:{pid}"
        now = time()
        allowforthistime = False
        if key in self.access_records:
            value, allow = self.access_records[key]
            # this 30 seconds is a magic number for now
            if now - value < 30:
                if not allow:
                    return False
                else:
                    allowforthistime = True
        # if allowed then continue reading
        if not allowforthistime:
            try:
                result = self.callback(display_path, process_name)
            except:
                self.access_records[key] = (now, False)
                return False
            if result != "okay":
                self.access_records[key] = (now, False)
                return False

        # store the value for the next read call
        self.access_records[key] = (now, True)
        return True


class FSThread(QThread):
    signal = pyqtSignal("PyQt_PyObject", "PyQt_PyObject")

    def __init__(self, mountpath="", password=""):
        QThread.__init__(self)
        self.mountpath = mountpath
        home = str(Path.home())
        storagepath = os.path.join(home, ".manualbox")
        key = password.encode("utf-8")
        self.fs = ManualBoxFS(
            key=key,
            mountpath=self.mountpath,
            storagepath=storagepath,
            callback=self.ask,
        )

    def ask(self, display_path, process_name):
        logging.debug(f"ASK called with {display_path} and {process_name}")
        self.signal.emit(display_path, process_name)
        return self.result

    def updateuserinput(self, result):
        self.result = result

    def run(self):
        try:
            self.fuse = FUSE(
                self.fs,
                self.mountpath,
                foreground=True,
                nothreads=True,
                allow_other=False,
            )
        except (ValueError, InvalidToken, binascii.Error):
            print("Wrong key for the ~/.manualbox")


class MainUserWindow(QMainWindow):
    userinput = pyqtSignal("PyQt_PyObject")
    CSS = """
            QLabel#filepath {
                color: black;
                font-size: 25px;
                background-color: rgb(255,255,255);
            }
            QPushButton#mountpathButton {
                background-color: rgb(255,255,255);
                font-size: 20px;
            }
            QPushButton#umountpathButton {
                background-color: rgb(255,255,255);
                font-size: 20px;
            }
            QPushButton {
                background-color: rgb(255,255,255);
            }


    """

    def __init__(self, parent=None):
        self.home = str(Path.home())
        self.path = os.path.join(self.home, "secured")
        storagepath = os.path.join(self.home, ".manualbox")
        self.mounted = False
        super(MainUserWindow, self).__init__(parent)
        self.layout = QVBoxLayout()

        iconlabel = QLabel(pixmap=QPixmap(get_asset_path("mainicon.png")))
        self.buttonslayout = QHBoxLayout()
        self.buttonslayout.addWidget(iconlabel)

        formlayout = QFormLayout()

        mountpathLabel = QLabel("Mount path  (empty for default):")
        self.mountpathTxt = MountEdit()

        passwordlabel = QLabel("Password:")
        self.passwordTxt = QLineEdit()
        self.passwordTxt.setEchoMode(QLineEdit.Password)

        formlayout.addRow(mountpathLabel, self.mountpathTxt)
        formlayout.addRow(passwordlabel, self.passwordTxt)
        form = QWidget()
        form.setLayout(formlayout)

        self.mountpathButton = QPushButton("Mount")
        self.mountpathButton.setObjectName("mountpathButton")
        self.mountpathButton.setFixedHeight(60)
        self.mountpathButton.setFixedWidth(100)
        self.mountpathButton.clicked.connect(self.mount)
        self.umountpathButton = QPushButton("Unmount")
        self.umountpathButton.setObjectName("umountpathButton")
        self.umountpathButton.setFixedHeight(60)
        self.umountpathButton.setFixedWidth(100)
        self.umountpathButton.clicked.connect(self.unmount)
        self.umountpathButton.hide()
        self.buttonslayout.addWidget(form)

        self.buttonslayout.addWidget(self.mountpathButton)
        self.buttonslayout.addWidget(self.umountpathButton)
        buttons = QWidget()
        buttons.setLayout(self.buttonslayout)
        self.layout.addWidget(buttons)
        self.textarea = QTextEdit()
        self.textarea.setReadOnly(True)
        self.layout.addWidget(self.textarea)
        mainw = QWidget()
        mainw.setLayout(self.layout)
        self.setCentralWidget(mainw)
        self.setFixedWidth(900)
        self.setFixedHeight(480)
        self.fs = None
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(QPixmap(get_asset_path("trayicon.png"))))

        self.quitAction = QAction("Exit", self)
        self.quitAction.triggered.connect(self.handleQuit)
        self.trayMenu = QMenu()
        self.trayMenu.addAction(self.quitAction)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.activated.connect(self.view_toggle)
        self.trayIcon.show()
        self.setStyleSheet(self.CSS)
        self.setWindowTitle("ManualBox")

        # now check if we have a ~/.manualbox
        if not os.path.exists(storagepath):
            msg = f"Creating a new ManualBox storage at: {storagepath}: "
            self.addText(msg)

            key = Fernet.generate_key()
            key_text = key.decode("utf-8")
            self.addText(f"Here is your new key, please store it securely: {key_text}")
            self.passwordTxt.setText(key_text)
            # now call mount
            self.mount()

    def view_toggle(self, reason):
        "To handle clicks on the tray icon"
        if reason == 1:
            self.trayMenu.show()
            return
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def closeEvent(self, event):
        "MainWindow closing event"
        if not self.mounted:
            qApp.quit()
        else:
            event.ignore()
            self.hide()
            self.trayIcon.showMessage(
                "ManualBox",
                "Application was minimized to Tray",
                QSystemTrayIcon.Information,
                2000,
            )

    def addText(self, newtext):
        text = self.textarea.toPlainText() + "\n"
        text += newtext
        self.textarea.setText(text)

    def handleQuit(self):
        if self.mounted:
            self.trayIcon.showMessage(
                "ManualBox",
                "Please unmount first and then quit.",
                QSystemTrayIcon.Information,
                5000,
            )
        else:
            qApp.quit()

    def msg_show(self, text):
        self.trayIcon.showMessage("ManualBox", text, QSystemTrayIcon.Information, 2000)

    def mount(self):
        "Mounts the provided path"
        self.path = str(self.mountpathTxt.text())
        if not self.path:
            self.path = os.path.join(self.home, "secured")
            try:
                os.mkdir(self.path)
            except FileExistsError:
                pass
            self.mountpathTxt.setText(self.path)

        # Now verify that the mount path exists
        if not os.path.exists(self.path):
            self.textarea.setText(
                f'The mount path <font color="red"><b>{self.path}</b></font> does not exist.'
            )
            return
        # Verify that the mount path is empty
        if len(os.listdir(self.path)) != 0:
            self.textarea.setText(
                f'The mount path <font color="red"><b>{self.path}</b></font> is not empty. Please select an empty directory.'
            )
            return

        password = str(self.passwordTxt.text())

        try:
            self.fs = FSThread(self.path, password)
        except (ValueError, InvalidToken, binascii.Error):
            self.textarea.setText(
                "Wrong password for the ~/.manualbox storage. Please try again."
            )
            return
        self.fs.signal.connect(self.asktheuser, QtCore.Qt.BlockingQueuedConnection)
        self.userinput.connect(self.fs.updateuserinput)
        self.fs.start()
        self.mountpathButton.hide()
        self.umountpathButton.show()
        self.passwordTxt.setEnabled(False)
        self.mountpathTxt.setEnabled(False)
        self.mounted = True
        self.addText(f"Successfully decrypted and mounted at {self.path}")
        # On mac the UI is not updating properly otherwise
        self.repaint()

    def unmount(self):
        "Unmounts the filesystem"
        self.fs.fs.saveondisk()

        try:
            if self.fs.fs.platform == "Darwin":
                subprocess.check_output(["diskutil", "unmount", "force", self.path])
            else:
                subprocess.check_output(["fusermount", "-u", self.path])
        except subprocess.CalledProcessError:
            self.addText(
                "Error while unmounting, please close any file browser opened on the mounted path and then try again."
            )
            return
        self.textarea.setText(
            """Unmounted successfully.

Encrypting the data into the storage on disk.
Encryption and storage is successful.
To use again, please click on the Mount button."""
        )
        self.passwordTxt.setEnabled(True)
        self.mountpathTxt.setEnabled(True)
        self.umountpathButton.hide()
        self.mountpathButton.show()
        self.mounted = False
        self.repaint()

    def asktheuser(self, display_path, process_name):
        logging.debug(f"ASKTHEUSER called with {display_path}")
        self.msg_show(f"Accesing: {display_path}")
        result = manualboxinput.main(display_path, process_name)
        # On mac the UI is not updating properly otherwise
        self.userinput.emit(result)


def main():
    logging.basicConfig(level=logging.INFO, filename="/dev/null")
    app = QtWidgets.QApplication(sys.argv)
    form = MainUserWindow()
    form.show()
    form.setWindowState(Qt.WindowState.WindowActive)
    form.raise_()
    app.exec_()


if __name__ == "__main__":
    main()
