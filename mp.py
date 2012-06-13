#!/usr/bin/env python

# Globals {{{1
mediaFileExtensions = ['flac', 'mp3', 'ogg'] # use lower case only
assert 'm3u' not in mediaFileExtensions

# Process command line {{{1
# Command line processing must be performed before importing gstreamer otherwise
# it tries to handle the command line options.
from cmdline import commandLineProcessor
from kskutils import conjoin, wrap

clp = commandLineProcessor()
clp.setDescription('Music Player', wrap(['''\
    Plays any music files given on its command line. If either a play list (m3u
    file) or a  directory is given, it will be recursively searched for music
    files, which will be added to the list of songs to be played.
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
opt = clp.addOption(
    key='help', shortName='h', longName='help', action=clp.printHelp
)
clp.process()
opts = clp.getOptions()
args = clp.getArguments()
quiet = 'quiet' in clp.getOptions()
repeat = 'repeat' in clp.getOptions()
shuffle = 'shuffle' in clp.getOptions()

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
                else:
                    if not self.quiet:
                        print "%s: skipping file of unknown type." % path
            elif isDir(path):
                self.addSongs(sorted(getAll(makePath(path, '*'))))
            else:
                if not self.quiet:
                    print "%s: skipping descriptor of unknown type." % path

    def shuffleSongs(self):
        from random import shuffle
        shuffle(self.songs)

    def play(self):
        import time
        from fileutils import absPath, normPath
        for song in self.songs:
            self.playing = True
            if not self.quiet:
                print normPath(song)
            self.player.set_property("uri", "file://" + absPath(song))
            self.player.set_state(gst.STATE_PLAYING)
            while self.playing:
                time.sleep(1)
        time.sleep(1)
        loop.quit()

# Construct and initialize player {{{1
import thread, gobject, glib
player = Player(quiet)
player.addSongs(args)

# Run the player {{{1
first = True
try:
    while first or repeat:
        if shuffle:
            player.shuffleSongs()
        thread.start_new_thread(player.play, ())
        gobject.threads_init()
        loop = glib.MainLoop()
        loop.run()
        first = False
except KeyboardInterrupt:
    if not quiet:
        print "%s: killed at user request." % clp.progName()
    exit()
