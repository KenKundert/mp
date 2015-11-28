# Player

# Imports {{{1
from __future__ import print_function, unicode_literals, absolute_import
from scripts import (
    abspath, exists, extension, fopen, head, isdir, isfile, join, ls,
    normpath
)
from .prefs import mediaFileExtensions, skipSongThatWasPlayingWhenLastKilled
from .metadata import MetaData
from time import sleep
import sys
try:
    import thread
except ImportError:
    import _thread
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
Gst.init(None)

# Player constructor{{{1
class Player(object):
    def __init__(self, quiet=False, now_playing_file = None):
        player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)
        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.processMessage)
        self.player = player
        self.quiet = quiet
        self.now_playing_file = now_playing_file
        self.songs = []
        self.skip = []
        self.played = []
        self.playing = False

    # processMessage() {{{1
    def processMessage(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playing = False
        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.playing = False

    # addSongs() {{{1
    def addSongs(self, paths, cwd='.'):
        for path in paths:
            path = normpath(join(cwd, path))
            if isfile(path):
                ext = extension(path).lower()
                if ext in mediaFileExtensions:
                    self.songs += [path]
                elif ext == '.m3u':
                    with fopen(path) as playlist:
                        lines = [l.strip() for l in playlist.readlines()]
                        self.addSongs(
                            [l for l in lines if l and l[0] != '#'],
                            head(path)
                        )
                elif exists(path):
                    if not self.quiet:
                        #print("%s: skipping descriptor of unknown type." % path)
                        pass
                else:
                    if not self.quiet:
                        print("%s: no such file or directory." % path)
            elif isdir(path):
                self.addSongs(sorted(ls(path=path)))

    # writePlaylist() {{{1
    def writePlaylist(self, filename):
        with fopen(filename, 'w') as playlist:
            playlist.write('\n'.join(self.songs))

    # addSkips() {{{1
    def addSkips(self, paths):
        self.skip = paths

    # shuffleSongs() {{{1
    def shuffleSongs(self):
        from random import shuffle
        shuffle(self.songs)

    # play() {{{1
    def play(self, quit):
        for song in self.songs:
            if song in self.skip:
                continue
            if skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
            self.playing = True
            if not self.quiet:
                metadata = MetaData(song, self.now_playing_file)
                print(metadata.summary())
                metadata.now_playing()
            self.player.set_property("uri", "file://" + abspath(song))
            self.player.set_state(Gst.State.PLAYING)
            while self.playing:
                sleep(0.1)
            if not skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
        self.skip = []
        self.played = []
        sleep(1)
        quit()

    # songsAlreadyPlayed() {{{1
    def songsAlreadyPlayed(self):
        return self.skip + self.played
