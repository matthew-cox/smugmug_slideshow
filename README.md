**Last Updated: 2018-06-01 19:58 @matthew-cox**

Table of Contents
=================
  * [SmugMug Slideshow](#smugmug-slideshow)
    * [Requirements](#requirements)
      * [macOS with Pyenv and Virtualenv](#macos-with-pyenv-and-virtualenv)
      * [Raspbian with System Python3](#raspbian-with-system-python3)
      * [Raspbian with Pyenv and Virtualenv](#raspbian-with-pyenv-and-virtualenv)
    * [Commandline Options](#commandline-options)
    * [Run the slide show](#run-the-slide-show)

# SmugMug Slideshow

Image slideshow from a SmugMug RSS Feed using Pygame

## Requirements

To start, you will need a recent Python 3.x with Pygame and a few other nicities

### macOS with Pyenv and Virtualenv

Highly reccommend using [brew](https://brew.sh) to install [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv):

    $ brew install pyenv pyenv-virtualenv

  Once you have that configured, launch a new iTerm and do the following:

    # install newish python 3.6.x
    $ pyenv install 3.6.5

    # create a repo specific virtualenv
    $ pyenv virtualenv 3.6.5 smugmug-slideshow-3.6.5

    # switch to the new virtualenv
    $ pyenv local smugmug-slideshow-3.6.5

    # ensure that pip and setuptools are new
    $ pip install --upgrade pip setuptools

    # install all the requirements
    $ pip install -r ./requirements.txt
    ...

### Raspbian with System Python3

Building Python from scratch can be taxing on a RaspberryPi. Fortunately, there are prebuilt packages for needed dependencies:

    # verify what will be installed
    $ grep -v '^#' raspbian-python3.deps
    pylint3
    python3-exif
    python3-feedparser
    python3-pil
    python3-pygame
    python3-requests

    # install the dependencies
    $ sudo apt-get install $(grep -v '^#' raspbian-python3.deps)

    # install speedparser for speed
    $ pip3 install --user speedparser3


### Raspbian with Pyenv and Virtualenv

To build Python and Pygame, one must install a bunch of build dependencies:

    # verify what will be installed
    $ grep -v '^#' raspbian-build.deps
    ffmpeg
    libavcodec-dev
    libavformat-dev
    libjpeg-dev
    libpng-dev
    libportmidi-dev
    libsdl-dev
    libsdl-image1.2-dev
    libsdl-mixer1.2-dev
    libsdl-ttf2.0-dev
    libsdl-ttf2.0-dev
    libsmpeg-dev
    libswscale-dev

    # install the build deps
    $ sudo apt-get install $(grep -v '^#' raspbian-build.deps)

After the build deps are installed: follow the [macOS instructions](#macos-with-pyenv-and-virtualenv) above.

## Commandline Options

    $ ./slideshow.py -h
    usage: slideshow.py [-h] (-g GALLERY_ID | -u GALLERY_URL) [--debug] [-d]
                        [-l {debug,info,warning,error,critical}] [--show-time SHOW_TIME]

    Run a slideshow of a SmugMug gallery

    optional arguments:
      -h, --help            show this help message and exit
      -g GALLERY_ID, --gallery-id GALLERY_ID
                            Gallery Id to display
      -u GALLERY_URL, --gallery-url GALLERY_URL
                            URL of Gallery to display
      --debug               Enable debug mode. Increases verbosity and shortens show time.
      -d, --downscale-only  Enable downscale mode. Prefer images larger than the display.
                            Default: False
      -l {debug,info,warning,error,critical}, --log-level {debug,info,warning,error,critical}
                            Logging verbosity. Default: WARNING
      --show-time SHOW_TIME
                            Time in milliseconds to show image. Default: 45000

## Run the slide show

    $ ./slideshow.py -u 'https://your-great-site.com/the/best/gallery'

