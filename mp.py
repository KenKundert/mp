#!/usr/bin/env python

# Imports {{{1
from config import (
    mediaFileExtensions, restartFilename, separator,
    skipSongThatWasPlayingWhenLastKilled
)
from cmdline import CommandLineProcessor
from kskutils import conjoin, wrap
from fileutils import exists, remove, getExt
import sys

# Globals {{{1
skip = []
restartArgs = []
restartOptions = []

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
                else:
                    if not self.quiet:
                        print "%s: skipping file of unknown type." % path
            elif isDir(path):
                self.addSongs(sorted(getAll(makePath(path, '*'))))
            elif exists(path):
                if not self.quiet:
                    print "%s: skipping descriptor of unknown type." % path
            else:
                if not self.quiet:
                    print "%s: no such file or directory." % path

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
        from fileutils import absPath, relPath
        for song in self.songs:
            if song in self.skip:
                continue
            if skipSongThatWasPlayingWhenLastKilled:
                self.played.append(song)
            self.playing = True
            if not self.quiet:
                print relPath(song)
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

# write out restart information
try:
    with open(restartFilename, 'w') as restartFile:
        restartFile.write('\n'.join(cmdLine[1:]) + '\n')
        restartFile.write(separator + '\n')
        restartFile.write('\n'.join(songsAlreadyPlayed))
except IOError, err:
    exit("%s: %s." % (err.filename, err.strerror))
