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

from cryptography.fernet import Fernet, InvalidToken

try:
    # This is for Debian/Ubuntu
    from fusepy import FUSE, FuseOSError, Operations, LoggingMixIn
except ModuleNotFoundError:
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class ManualBoxFS(LoggingMixIn, Operations):
    """
    ManualBoxFS will stay on memory till it is closed.
    """

    error = True

    def __init__(self, key=b"", mountpath="", storagepath=""):
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
        print(f"\nYour storage is now mounted at {mountpath}. Press Ctrl+C to unmount.")

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
        names = [".", ".."] + [x[1:] for x in self.files if x != "/"]
        for name in names:
            yield name

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
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

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
        "We will have to save the Filesystem on disk here."
        # This is incase of an error in decryption of the ~/.manualbox
        if self.error:
            return

        # First dump into pickle
        localdata = pickle.dumps((self.files, self.data))
        # Now, we encrypt
        print("\nEncrypting the data into the storage on disk.")
        encrypted = self.locker.encrypt(localdata)

        # Now, write it on the disk
        with open(self.storagepath, "wb") as fobj:
            fobj.write(encrypted)
        print("Encryption and storage is successful.")

    def manualquestion(self, path, fh):
        if self.platform == "Darwin":
            cmdpath = "/usr/local/bin/manualboxinput"
        else:
            cmdpath = "/usr/bin/manualboxinput"
        logging.debug(f"manualquestion is called for {path} with {fh}")
        display_path = os.path.join(self.mountpath, path[1:])
        key = f"{path}:{fh}"
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
                result = subprocess.check_output([cmdpath, display_path])
            except:
                self.access_records[key] = (now, False)
                return False
            if result != b"okay\n":
                self.access_records[key] = (now, False)
                return False

        # store the value for the next read call
        self.access_records[key] = (now, True)
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mount")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, filename="/tmp/test.log")
    home = str(Path.home())
    storagepath = os.path.join(home, ".manualbox")
    if os.path.exists(storagepath):
        msg = f"Provide the key for the existing ManualBox storage at: {storagepath}: "
        password = getpass.getpass(msg)
        key = password.encode("utf-8")
    else:
        msg = f"Creating a new ManualBox storage at: {storagepath}: "
        print(msg)
        timemodule.sleep(1)
        key = Fernet.generate_key()
        print(f"Here is your new key, please store it securely: {key}")
    try:
        fuse = FUSE(
            ManualBoxFS(key=key, mountpath=args.mount, storagepath=storagepath),
            args.mount,
            foreground=True,
            nothreads=True,
            allow_other=False,
        )
    except (ValueError, InvalidToken, binascii.Error):
        print("Wrong key for the ~/.manualbox")
        sys.exit(-3)


if __name__ == "__main__":
    main()

