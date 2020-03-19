# ManualBox

ManualBox is a command line for the desktop users to create/mount an userspace file system, where reading
of any file will require user input via a GUI tool.

## Installation/Usage for development purpose

First we will need all the dependencies:

### On Debian

```sh
sudo apt install python3-cryptography python3-pyqt5 python3-fusepy
```

Now, for development purpose, you will have to create a symlink to our user input script into `/usr/bin/`

```sh
sudo ln -s $PWD/devscripts/manualboxinput /usr/bin/manualboxinput
```

### On Mac

First install the [FUSE for Mac](https://osxfuse.github.io/) with Macfuse layer.

Then install Python3.7.6 from https://python.org

After this, install `poetry`.

```sh
pip3 install --user poetry
```

Then install the tool locally:

```sh
poetry install
```

Now, for development purpose, you will have to create a symlink to our user input script into `/usr/local/bin/`

```sh
sudo ln -s $PWD/devscripts/manualboxinput /usr/local/bin/manualboxinput
```

Note: On Mac, the system will ask for user input when any tool will try to open the file for both reading and writing.

### Usage

When you run the tool for the first time, it will create a new encryption key for your `~/.manualbox` file.
Please store it securely somewhere.

```sh
./devscripts/manualbox /path/where/we/will/mount
```

Example, to mount at `/home/kdas/secured` I will execute:

```sh
./devscripts/manualbox /home/kdas/secured
```

In the first run, it will give you the key for your encrypted storage, keep the key safe as you can not access your files without the key.

Note: The current implementation of the filesystem can only store files in the top level directory, this will be fixed in the coming days.

## License

GPLv3+
