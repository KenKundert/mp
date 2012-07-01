====
 mp
====

------------
music player
------------

:Author: Ken Kundert <mp@shalmirane.com>
:Date: {date}
:Copyright: public domain
:Version: {version}
:Manual section: 1
:Manual group: Multimedia

SYNOPSIS
========
mp [ options ] args ...

DESCRIPTION
===========
``mp`` plays any music files given on its command line. If either a play list
(m3u file) or a  directory is given, it will be recursively searched
for music files, which will be added to the list of songs to be
played.

Currently only {extensions} music files are supported.

Use Ctrl-Z to pause and 'fg' to continue. Use Ctrl-C when running to kill.

OPTIONS
=======

-1, --quiet     Do not print name of the music file being played.
-r, --repeat    Repeat songs.
-s, --shuffle   Shuffle songs.  If combined with repeat, the songs will be
                shuffled before each repeat.
-p <filename.m3u>, --playlist <filename.m3u>
                Generate a playlist from the music specified rather than play
                the music.

If invoked with no arguments or options ``mp`` will repeat the session that was 
previously run in the same directory, skipping any songs that had already been 
played.
