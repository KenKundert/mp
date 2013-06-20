mp: A Music Player
==================

This is a simple command line music player. It will play individual music files 
(flac, mp3, ogg, and wav), directories that contain music files, and m3u play 
lists.

Tested with Python version 2.7 under Fedora Linux. You will need install the 
docutils, gstreamer, mutagen packages for python with::

    yum install python-docutils gstreamer-python gstreamer-plugins-good mutagen

If you want mp3 support, you also need to install the 'ugly' plugins from the 
RPM Fusion non-free repository::

    yum install gstreamer-plugins-ugly

If you do not want mp3 support, edit config.py and remove 'mp3' from 
mediaFileExtensions.

To get the source code::

    $ git clone git://github.com/KenKundert/mp.git

Once cloned, you can get the latest updates using::

    $ git pull

To install::

    $ ./install

Be sure to add ~/.local/bin to your PATH.

To read the MP manual::

    $ man mp

To run MP::

    $ mp music-files