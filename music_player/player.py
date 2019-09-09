# Player

# Imports {{{1
from .prefs import (
    media_file_extensions, restart_path,
    skip_song_that_was_playing_when_last_killed
)
from .metadata import MetaData
from inform import display, Error, join, warn
from pathlib import Path
from time import sleep
try:
    import thread
except ImportError:
    import _thread
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
Gst.init(None)
import sys

# Player constructor{{{1
class Player(object):
    def __init__(self, now_playing_path = None, informer=None):
        player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        player.set_property("video-sink", fakesink)
        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._process_message)
        self.player = player
        self.informer = informer
        self.now_playing_path = now_playing_path
        self.songs = []
        self.skip = []
        self.played = []
        self.playing = False

    # _process_message() (private) {{{1
    def _process_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playing = False
        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            raise Error("Error: %s" % err, debug)
            self.playing = False

    # add_songs() {{{1
    def add_songs(self, paths, cwd='.'):
        for path in paths:
            path = Path(cwd, path).expanduser()
            if path.is_file():
                ext = path.suffix.lower()
                if ext in media_file_extensions:
                    self.songs += [str(path)]
                elif ext == '.m3u':
                    try:
                        playlist = path.read_text()
                        lines = [l.strip() for l in playlist.splitlines()]
                        self.add_songs(
                            [l for l in lines if l and l[0] != '#'],
                            path.parent
                        )
                    except OSError as e:
                        raise Error(os_error(e))
                elif path.stem != restart_path.stem:
                    if not self.informer.quiet:
                        warn('skipping descriptor of unknown type.', culprit=path)
            elif path.is_dir():
                self.add_songs(path.iterdir())
            else:
                if not self.informer.quiet:
                    warn('not found.', culprit=path)
        if not self.songs:
            raise Error('playlist is empty.')

    # write_playlist() {{{1
    def write_playlist(self, path):
        try:
            path.write_text(join(*self.songs))
        except OSError as e:
            raise Error(os_error(e))

    # add_skips() {{{1
    def add_skips(self, paths):
        self.skip = paths

    # shuffle_songs() {{{1
    def shuffle_songs(self):
        from random import shuffle
        shuffle(self.songs)

    # play() {{{1
    def play(self, quit):
        for song_filename in self.songs:
            if song_filename in self.skip:
                continue
            if skip_song_that_was_playing_when_last_killed:
                self.played.append(song_filename)
            self.playing = True
            song_path = Path(song_filename).expanduser()
            metadata = MetaData(song_path, self.now_playing_path)
            metadata.now_playing()
            display(metadata.summary())
            self.player.set_property("uri", "file://" + str(song_path.resolve()))
            self.player.set_state(Gst.State.PLAYING)
            while self.playing:
                sleep(0.1)
            if not skip_song_that_was_playing_when_last_killed:
                self.played.append(song_filename)
        self.skip = []
        self.played = []
        sleep(1)
        quit()

    # songs_already_played() {{{1
    def songs_already_played(self):
        # iterate though songs already played without repeating.
        #played = self.skip + self.played
        #seen = set()
        #return [n for n in played if not (n in seen or seen.add(n))]
        return list(dict.fromkeys(self.skip + self.played))
