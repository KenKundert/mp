#!/usr/bin/env python

# Music Player {{{1
# Copyright (C) 2013 Kenneth S. Kundert
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
from config import (
    mediaFileExtensions, restartFilename, separator,
    skipSongThatWasPlayingWhenLastKilled
)
from cmdline import CommandLineProcessor
from kskutils import conjoin, wrap, cull
from fileutils import exists, remove, getExt, absPath, relPath, expandPath
import sys

# Globals {{{1
now_playing_file = '~/.nowplaying'
    # if now_playing_file is set, the artist and song title will be placed in 
    # that file while that song is playing.
skip = []
restartArgs = []

# process the globals
now_playing_file = expandPath(now_playing_file)

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
        exit('Previous session information not found.')

clp = CommandLineProcessor(cmdLine)
clp.setDescription('Music Player', wrap(['''\
    Plays any music files given on its command line. If either a play list (m3u
    file) or a  directory is given, it will be recursively searched for music
    files, which will be added to the list of songs to be played.
''', '''\
    If invoked with no arguments or options mp will repeat the session that was
    previously run in the same directory, skipping any songs that had already
    been played.
''', '''\
    Music files with the following extensions are supported: '%s'.
''' % conjoin(mediaFileExtensions, conj="' and '", sep="', '")
]))
clp.setNumArgs((0,), 'songs ...')
clp.setHelpParams(key='--help', colWidth=15)
opt = clp.addOption(key='quiet', shortName='q', longName='quiet')
opt.setSummary('Do not print name of the music file being played.')
opt = clp.addOption(key='repeat', shortName='r', longName='repeat')
opt.setSummary('Repeat songs.')
opt = clp.addOption(key='shuffle', shortName='s', longName='shuffle')
opt.setSummary(wrap(['''\
    Shuffle songs.
    If combined with repeat, the songs will be shuffled before each repeat.
''']))
opt = clp.addOption(key='playlist', shortName='p', longName='playlist')
opt.setNumArgs(1, '<filename.m3u>')
opt.setSummary(wrap(['''\
    Generate a playlist from the music specified rather than play the music.
''']))
opt = clp.addOption(
    key='help', shortName='h', longName='help', action=clp.printHelp
)
clp.process()
opts = clp.getOptions()
args = clp.getArguments()
quiet = 'quiet' in opts
repeat = 'repeat' in opts
shuffle = 'shuffle' in opts
playlist = opts.get('playlist', None)

# MetaData class {{{1
# I have a very weak understanding of the way metadata is implemented and why
# this is so hard.
class MetaData:
    def __init__(self, filename):
        self.filename = relPath(filename)
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
        ext = getExt(filename).lower()
        if ext == 'ogg':
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
        elif ext == 'mp3':
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
        elif ext == 'flac':
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
            out = []
            for each in [self.artist, self.title]:
                out += [each]
            try:
                with open(now_playing_file, 'w') as f:
                    f.write(' - '.join(cull(out)))
            except IOError, err:
                exit("%s: %s." % (err.filename, err.strerror))

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
    def __init__(self, quiet = False):
        player = gst.element_factory_make("playbin2", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)
        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.processMessage)
        self.player = player
        self.quiet = quiet
        self.songs=[]
        self.skip=[]
        self.played=[]

    def processMessage(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.playing = False
        elif message.type == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.playing = False

    def addSongs(self, paths, cwd=''):
        from fileutils import isFile, isDir, getAll, getExt, getHead, makePath
        for path in paths:
            path = makePath(cwd, path.strip())
            if isFile(path):
                ext = getExt(path).lower()
                if ext in mediaFileExtensions:
                    self.songs += [path]
                elif ext == 'm3u':
                    with open(path) as playlist:
                        self.addSongs(playlist, getHead(path))
                elif exists(path):
                    if not self.quiet:
                        print "%s: skipping descriptor of unknown type." % path
                else:
                    if not self.quiet:
                        print "%s: no such file or directory." % path
            elif isDir(path):
                self.addSongs(sorted(getAll(makePath(path, '*'))))

    def writePlaylist(self, filename):
        with open(filename, 'w') as playlist:
            playlist.write('\n'.join(self.songs))

    def addSkips(self, paths):
        self.skip = paths

    def shuffleSongs(self):
        from random import shuffle
        shuffle(self.songs)

    def play(self):
        import time
        for song in self.songs:
            if song in self.skip:
                continue
            if skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
            self.playing = True
            if not self.quiet:
                metadata = MetaData(song)
                print metadata.summary()
                metadata.now_playing()
            self.player.set_property("uri", "file://" + absPath(song))
            self.player.set_state(gst.STATE_PLAYING)
            while self.playing:
                time.sleep(1)
            if not skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
        self.skip = []
        self.played = []
        time.sleep(1)
        loop.quit()

    def songsAlreadyPlayed(self):
        return self.skip + self.played

# Construct and initialize player {{{1
import thread, gobject, glib
player = Player(quiet)
player.addSongs(args)
if playlist:
    playlist = playlist[0]
    if not getExt(playlist):
        playlist += '.m3u'
    player.writePlaylist(playlist)
    print "Playlist written to '%s'." % playlist
    print wrap(["""\
        To create a tar file that contains the playlist and the music files it
        references, run:
    """])
    print "    tar zcfT %s.tgz %s %s" % (
        playlist.rsplit('.')[0], playlist, playlist
    )
    exit()
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
            print "Rewinding ..."
except KeyboardInterrupt:
    if not quiet:
        print "%s: killed at user request." % clp.progName()
    songsAlreadyPlayed = player.songsAlreadyPlayed()

try:
    if now_playing_file:
        remove(now_playing_file)
    # write out restart information
    with open(restartFilename, 'w') as restartFile:
        restartFile.write('\n'.join(cmdLine[1:]) + '\n')
        restartFile.write(separator + '\n')
        restartFile.write('\n'.join(songsAlreadyPlayed))
except IOError, err:
    exit("%s: %s." % (err.filename, err.strerror))
