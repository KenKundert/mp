mp: A Music Player
==================

This is a simple command line music player. It will play individual music files 
(flac, mp3, ogg, oga, and wav), directories that contain music files, and m3u 
play lists.

Requires Python and 3.6 or better. You will need install the docutils, Gobject, 
gstreamer, and mutagen packages for Python. For Fedora, use::

   dnf install python3-gobject python3-gstreamer1 gstreamer-plugins-good
   pip3 install --user docutils mutagen

For Arch, use::

   pacman -S python-gobject gtk3 gstreamer gst-plugins-base gst-plugins-good gst-libav
   pip3 install --user docutils mutagen

If you want mp3 support, you also need to install the 'ugly' plugins from the 
RPM Fusion non-free repository::

   yum install gstreamer1-plugins-ugly

If you do not want mp3 support, edit music_player/prefs.py and remove 'mp3' from 
media_file_extensions.

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
