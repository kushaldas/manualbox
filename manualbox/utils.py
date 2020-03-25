import os
import sys

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(file_name):
    "Return the absolute path for requested asset"
    # This is for development version and also for packaged in Linux
    path = os.path.join(BASE_PATH, "assets", file_name)
    if os.path.exists(path):
        return path
    # This should work in Linux 
    path = os.path.join(sys.prefix, "share/manualbox/assets", file_name)

    if os.path.exists(path):
        return path

    if sys.platform == "darwin":
        path = os.path.join(sys._MEIPASS, "share/assets", file_name)
        print(path)
        return path

    return ""
