# ManualBox

ManualBox is a command line for the desktop users to create/mount an userspace file system, where reading
of any file will require user input via a GUI tool.

## Installation/Usage for development purpose

First we will need all the dependencies:

On Debian

```sh
sudo apt install python3-cryptography python3-pyqt5 python3-fusepy
```

Now, for development purpose, you will have to create a symlink to our user input script into `/usr/bin/`

```sh
sudo ln -s $PWD/devscripts/manualboxinput /usr/bin/manualboxinput
```

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

## License

GPLv3+
