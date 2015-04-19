mp: A Music Player
==================

This is a simple command line music player. It will play individual music files 
(flac, mp3, ogg, and wav), directories that contain music files, and m3u play 
lists.

Tested with Python versions 2.7 and 3.3 under Fedora Linux. You will need 
install the docutils, GI, gstreamer, and mutagen packages for python with::

   yum install python-docutils python-gi gstreamer-python gstreamer-plugins-good
    
   pip install python-mutagen
   
or with python3

   pip3 install mutagen

If you want mp3 support, you also need to install the 'ugly' plugins from the 
RPM Fusion non-free repository::

   yum install gstreamer-plugins-ugly

With recent versions of Fedora I now seem to have to install more plugins to get 
MP3s to work. I am not sure of what a minimum set would be, but this seemed to 
fix the issue::

   yum install gstreamer-plugins-bad gstreamer-plugins-bad-free \
               gstreamer-plugins-bad-free-extras gstreamer-plugins-bad-nonfree \
               gstreamer-plugins-base gstreamer-plugins-espeak \
               gstreamer-plugins-good gstreamer-plugins-ugly \
               gstreamer1-plugins-bad-free gstreamer1-plugins-bad-free-extras \
               gstreamer1-plugins-bad-freeworld gstreamer1-plugins-base \
               gstreamer1-plugins-base-tools gstreamer1-plugins-good \
               gstreamer1-plugins-good-extras gstreamer1-plugins-ugly

If you do not want mp3 support, edit music_player/prefs.py and remove 'mp3' from 
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
