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
from __future__ import division, print_function
from config import (
    mediaFileExtensions, restartFilename, separator,
    skipSongThatWasPlayingWhenLastKilled
)
import docopt
from scripts import (
    abspath, addext, exists, extension, fopen, head, isdir, isfile, join, ls,
    normpath, rm, script_prefs, stem,
)
from time import sleep
import sys

# Globals {{{1
now_playing_file = join('~/.nowplaying', expanduser=True)
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

# Process command line {{{1
# Command line processing must be performed before importing gstreamer otherwise
# it tries to handle the command line options.
cmdLine = sys.argv
if len(cmdLine) == 1:
    # Command line is empty, try to restart
    try:
        with open(restartFilename) as restartFile:
            lines = restartFile.readlines()
        lines = [line.strip() for line in lines]
        for i, line in enumerate(lines):
            if line == separator:
                partition = i
                break
        else:
            # this file is not what we were expecting, ignore it
            raise IOError

        # augment command line with the saved version
        cmdLine += lines[:partition]
        # skip the songs that were already played
        skip = lines[partition+1:]
    except IOError:
        sys.exit('Previous session information not found.')

# Actually read the command line and save options
args = docopt.docopt(__doc__ % ', '.join(mediaFileExtensions), cmdLine)
quiet = args['--quiet']
repeat = args['--repeat']
shuffle = args['--shuffle']
playlist = args['--playlist']

# MetaData class {{{1
# I have a very weak understanding of the way metadata is implemented and why
# this is so hard.
class MetaData:
    def __init__(self, filename):
        self.filename = filename
        self.artist = None
        self.album = None
        self.title = None
        self.track = None
        self.volume = None

        # Try EasyID3 metadata
        try:
            from mutagen.easyid3 import EasyID3
            from mutagen.id3 import ID3NoHeaderError
            try:
                metadata = EasyID3(filename)
                self._getEasyMetadata(metadata)
                return
            except ID3NoHeaderError:
                pass
        except ImportError:
            pass

        # If that did not work, try ID3 metadata
        try:
            from mutagen.id3 import ID3, ID3NoHeaderError
            try:
                metadata = ID3(filename)
                self._getID3Metadata(metadata)
                return
            except ID3NoHeaderError:
                pass
        except ImportError:
            pass

        # If those did not work, filetype specific metadata
        ext = extension(filename).lower()
        if ext == '.ogg':
            try:
                from mutagen.oggvorbis import OggVorbis, OggVorbisHeaderError
                try:
                    metadata = OggVorbis(filename)
                    self._getEasyMetadata(metadata)
                    return
                except OggVorbisHeaderError:
                    pass
            except ImportError:
                pass
        elif ext == '.mp3':
            try:
                from mutagen.mp3 import MP3, HeaderNotFoundError
                try:
                    metadata = MP3(filename)
                    self._getID3Metadata(metadata)
                    return
                except HeaderNotFoundError:
                    pass
            except ImportError:
                pass
        elif ext == '.flac':
            try:
                from mutagen.flac import FLAC, FLACNoHeaderError
                try:
                    metadata = FLAC(filename)
                    self._getEasyMetadata(metadata)
                    return
                except FLACNoHeaderError:
                    pass
            except ImportError:
                pass
        # if we get here we failed to get the metadata

    def summary(self):
        if self.album:
            if self.volume and self.track:
                album = " (track %s.%s from '%s')" % (self.volume, self.track, self.album)
            elif self.track:
                album = " (track %s from '%s')" % (self.track.lstrip('0'), self.album)
            else:
                album = " (from '%s')" % (self.album)
        else:
            album = ''
        if self.artist and self.title:
            return "%s '%s'%s" % (self.artist, self.title, album)
        elif self.title:
            return "'%s'%s" % (self.title, album)
        else:
            return self.filename

    def now_playing(self):
        if now_playing_file:
            out = [each for each in [self.artist, self.title] if each]
            with fopen(now_playing_file, 'w') as f:
                f.write(' - '.join(out))

    def _getEasyMetadata(self, metadata):
        self.artist = metadata.get('artist', [None])[0]
        self.album = metadata.get('album', [None])[0]
        self.title = metadata.get('title', [None])[0]
        self.track = metadata.get('tracknumber', [None])[0]
        self.volume = metadata.get('discnumber', [None])[0]

    def _getID3Metadata(self, metadata):
        try:
            self.artist = metadata['TPE1'].text[0]
        except KeyError:
            pass
        try:
            self.album = metadata['TALB'].text[0]
        except KeyError:
            pass
        try:
            self.title = metadata['TIT2'].text[0]
        except KeyError:
            pass
        try:
            self.track = metadata['TRCK'].text[0]
        except KeyError:
            pass
        try:
            self.volume = metadata['TPOS'].text[0]
        except KeyError:
            pass

# Player class {{{1
# import gstreamer
import pygst
pygst.require("0.10")
import gst
    # With gnome3 this import generates a deprecated function warning
    # This warning can be ignored.

class Player:
    def __init__(self, quiet=False):
        player = gst.element_factory_make("playbin2", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)
        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.processMessage)
        self.player = player
        self.quiet = quiet
        self.songs = []
        self.skip = []
        self.played = []
        self.playing = False

    def processMessage(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.playing = False
        elif message.type == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.playing = False

    def addSongs(self, paths, cwd='.'):
        for path in paths:
            path = normpath(join(cwd, path))
            if isfile(path):
                ext = extension(path).lower()
                if ext in mediaFileExtensions:
                    self.songs += [path]
                elif ext == '.m3u':
                    with fopen(path) as playlist:
                        self.addSongs(
                            playlist.read().strip().split('\n'),
                            head(path)
                        )
                elif exists(path):
                    if not self.quiet:
                        print("%s: skipping descriptor of unknown type." % path)
                else:
                    if not self.quiet:
                        print("%s: no such file or directory." % path)
            elif isdir(path):
                self.addSongs(sorted(ls(path=path)))

    def writePlaylist(self, filename):
        with fopen(filename, 'w') as playlist:
            playlist.write('\n'.join(self.songs))

    def addSkips(self, paths):
        self.skip = paths

    def shuffleSongs(self):
        from random import shuffle
        shuffle(self.songs)

    def play(self):
        for song in self.songs:
            if song in self.skip:
                continue
            if skipSongThatWasPlayingWhenLastKilled:
                self.played.append(sont)
            self.playing = True
            if not self.quiet:
                metadata = MetaData(song)
                print(metadata.summary())
                metadata.now_playing()
            self.player.set_property("uri", "file://" + abspath(song))
            self.player.set_state(gst.STATE_PLAYING)
            while self.playing:
                sleep(1)
            if not skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
        self.skip = []
        self.played = []
        sleep(1)
        loop.quit()

    def songsAlreadyPlayed(self):
        return self.skip + self.played

# Construct and initialize player {{{1
import thread, gobject, glib
player = Player(quiet)
player.addSongs(args['<songs>'][1:])
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
        thread.start_new_thread(player.play, ())
        gobject.threads_init()
        loop = glib.MainLoop()
        loop.run()
        first = False
        if repeat and not quiet:
            print("Rewinding ...")
except KeyboardInterrupt:
    if not quiet:
        print("mp: killed at user request.")
    songsAlreadyPlayed = player.songsAlreadyPlayed()

if now_playing_file:
    rm(now_playing_file)

# write out restart information
with fopen(restartFilename, 'w') as restartFile:
    restartFile.write('\n'.join(cmdLine[1:]) + '\n')
    restartFile.write(separator + '\n')
    restartFile.write('\n'.join(songsAlreadyPlayed) + '\n')
