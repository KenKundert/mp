#!/usr/bin/env python
"""
Music Player

Plays any music files given on its command line. If either a play list
(m3u file) or a  directory is given, it will be recursively searched
for music files, which will be added to the list of songs to be
played.

If invoked with no arguments or options mp will repeat the session
that was previously run in the same directory, skipping any songs that
had already been played.

Music files with the following extensions are supported:
    %s.

Usage:
    mp [options] <songs> ...

Options:
    -q, --quiet      Do not print name of the music file being played.
    -r, --repeat     Repeat songs.
    -s, --shuffle    Shuffle songs. If combined with repeat, the songs will be
                     shuffled before each repeat.
    -p, --playlist <filename.m3u>
                     Generate a playlist from the music specified rather than
                     play the music.
"""

# License {{{1
# Copyright (C) 2014 Kenneth S. Kundert
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

# Imports {{{1
from __future__ import print_function, unicode_literals, absolute_import
from music_player import (
    MetaData,
    Player,
    mediaFileExtensions,
    restartFilename,
    separator,
    nowPlayingFilename,
)
import docopt
from scripts import (
    abspath, addext, exists, extension, fopen, head, isdir, isfile, join, ls,
    normpath, rm, script_prefs, stem, ScriptError
)
from time import sleep
import threading
from gi.repository import GObject, Gst
GObject.threads_init()
Gst.init(None)
import sys

# Globals {{{1
assert 'm3u' not in mediaFileExtensions
if nowPlayingFilename:
    now_playing_file = join(nowPlayingFilename, expanduser=True)
else:
    now_playing_file = None
    # if now_playing_file is set, the artist and song title will be placed in 
    # that file while that song is playing.
skip = []
restartArgs = []
script_prefs.set('exit_upon_error', False)
    # normally this should be set to true because the ScriptError exception is
    # not caught by this program, but there is something wrong with the threads
    # and the program simply hangs if exit is called unexpectedly and there is
    # no indication of what when wrong. With it set to False at least a stack
    # trace is printed so you can figure out what when wrong.
cmdLine = sys.argv

# Read restart file {{{1
# Command line processing must be performed before importing gstreamer otherwise
# it tries to handle the command line options.
if len(cmdLine) == 1:
    # Command line is empty, try to restart
    try:
        with fopen(restartFilename) as restartFile:
            lines = restartFile.readlines()
        lines = [line.strip() for line in lines]
        for i, line in enumerate(lines):
            if line == separator:
                partition = i
                break
        else:
            # this file is not what we were expecting, ignore it
            raise ScriptError

        # augment command line with the saved version
        cmdLine += lines[:partition]
        # skip the songs that were already played
        skip = lines[partition+1:]
    except ScriptError:
        sys.exit('Previous session information not found.')

# Process command line {{{1
try:
    unicode
    cmdLine = [str(arg) for arg in cmdLine]
except NameError:
    pass
    # This code should not be necessary, but is because docopt does not
    # support unicode yet, but it does support python3 where all strings are
    # unicode. This code converts command line args from unicode to simple
    # strings, but in python3 where it is not necessary unicode is not
    # defined, and that triggers the NameError. So in python2 the arguments
    # are converted to strings, in python3 they are left as unicode.
    # Reports are that docopt is being fixed, so this should go away soon
    # (current version is 0.6.1.1).
args = docopt.docopt(__doc__ % ', '.join(mediaFileExtensions), cmdLine)
quiet = args['--quiet']
repeat = args['--repeat']
shuffle = args['--shuffle']
playlist = args['--playlist']
songs = args['<songs>'][1:]

# Construct and initialize player {{{1
player = Player(quiet, now_playing_file)
player.addSongs(songs)
if playlist:
    if not extension(playlist):
        playlist = addext(playlist, '.m3u')
    player.writePlaylist(playlist)
    print('\n'.join([
        "Playlist written to '%s'." % playlist,
        "To create a tar file that contains the playlist and the music files",
        "it references, run:",
        "    tar zcfT %s.tgz %s %s" % (
            stem(playlist), playlist, playlist
        )
    ]))
    sys.exit()
player.addSkips(skip)

# Run the player {{{1
first = True
songsAlreadyPlayed = []
try:
    while first or repeat:
        if shuffle:
            player.shuffleSongs()
        loop = GObject.MainLoop()
        thread = threading.Thread(target=player.play, args=(loop.quit,))
        thread.setDaemon(True)
        thread.start()
        loop.run()
        first = False
        if repeat and not quiet:
            print("Rewinding ...")
except KeyboardInterrupt:
    if not quiet:
        print("mp: killed at user request.")
    songsAlreadyPlayed = player.songsAlreadyPlayed()

# Termination {{{1
if now_playing_file:
    rm(now_playing_file)

# write out restart information
with fopen(restartFilename, 'w') as restartFile:
    restartFile.write('\n'.join(cmdLine[1:]) + '\n')
    restartFile.write(separator + '\n')
    restartFile.write('\n'.join(songsAlreadyPlayed) + '\n')
