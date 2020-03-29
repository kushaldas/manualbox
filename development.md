# Development guideline

First we will need all the dependencies:

### On Debian

```sh
sudo apt install python3-cryptography python3-pyqt5 python3-fusepy
```

### On Fedora

```sh
sudo dnf install python3-cryptography python3-qt5 python3-fusepy -y
```

### On macOS

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up. Also, run this to make sure command line tools are installed: `xcode-select --install`. And finally, open Xcode, go to `Preferences > Locations`, and make sure under Command Line Tools you select an installed version from the dropdown. (This is required for installing Qt5.)

Install Qt 5.14.1 for macOS from https://www.qt.io/offline-installers. I downloaded `qt-opensource-mac-x64-5.14.1.dmg`. In the installer, and all you need is `Qt > Qt 5.14.1 > macOS`.

Then install the [FUSE for Mac](https://osxfuse.github.io/) with Macfuse layer.

Then install [Python 3.7.6](https://www.python.org/downloads/release/python-376/).

After this, install `poetry`.

```sh
pip3 install --user poetry
```

Then install the tool locally:

```sh
poetry install
```

Note: On Mac, the system will ask for user input when any tool will try to open the file for both reading and writing.

Remember to use `black` to format the code before you submit any PR.