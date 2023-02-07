#!/usr/bin/env python3
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
    mp [options] [<songs> ...]

Options:
    -t, --terse      Do not print name of the music file being played.
    -r, --repeat     Repeat songs.
    -s, --shuffle    Shuffle songs. If combined with repeat, the songs will be
                     shuffled before each repeat.
    -p, --playlist <filename.m3u>
                     Generate a playlist from the music specified rather than
                     play the music.
    --no-restart     Do not write restart file.
"""

# License {{{1
# Copyright (C) 2014-2023 Kenneth S. Kundert
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
# the threading package is throwing off a lot of deprecation warnings
# KSK 220224
import warnings
warnings.filterwarnings("ignore")

from music_player import (
    MetaData, Player, media_file_extensions, restart_path, separator,
    now_playing_path, __version__, __released__
)
from appdirs import user_data_dir
from docopt import docopt
from inform import (
    Error, Inform, display, done, error, fatal, join, narrate, os_error, output, 
    warn,
)
from pathlib import Path
from textwrap import dedent
from time import sleep
import threading
from gi.repository import GLib, Gst
Gst.init(None)
import sys

# Globals {{{1
assert 'm3u' not in media_file_extensions
skip = []
cmd_line = sys.argv
logfile = Path(user_data_dir('mp')) / 'log' 

# Music Player {{{1
with Inform(notify_if_no_tty=True, logfile=logfile, flush=True) as inform:

    # Read restart file {{{2
    # Command line processing must be performed before importing gstreamer
    # otherwise it tries to handle the command line options.
    args = cmd_line[1:]
    if args == [] or args == ['--terse']:
        # Command line is empty, try to restart
        narrate('command line is empty, reading', restart_path, end='.\n')
        try:
            restartFile = restart_path.read_text()
            lines = [line.strip() for line in restartFile.splitlines()]
            for i, line in enumerate(lines):
                if line == separator:
                    partition = i
                    break
            else:
                # file contents are not as expected
                raise Error('invalid restart file.', culprit=restart_path)

            # augment command line with the saved version
            cmd_line = cmd_line[0:1] + lines[:partition]
            # skip the songs that were already played
            skip = lines[partition+1:]
        except Error as e:
            e.terminate()
        except OSError as e:
            fatal(os_error(e))

    # Process command line {{{2
    args = docopt(
        __doc__ % ', '.join(media_file_extensions),
        argv = cmd_line,
        version = f'mp {__version__} ({__released__})',
    )
    repeat = args['--repeat']
    shuffle = args['--shuffle']
    playlist = args['--playlist']
    write_restart_file = not args['--no-restart']
    songs = args['<songs>'][1:]
    inform.quiet = args['--terse']

    # Construct and initialize player {{{2
    try:
        narrate('starting player in', Path.cwd())
        player = Player(now_playing_path, inform)
        player.add_songs(songs)
        if playlist:
            narrate('writing playlist:', playlist)
            playlist = Path(playlist).expanduser()
            if not playlist.suffix:
                playlist = playlist.with_suffix('.m3u')
            player.write_playlist(playlist)
            output(
                f"Playlist written to '{playlist!s}'.",
                'To create a tar file that contains the playlist and the',
                'music files it references, run:',
                f'    tar zcfT {playlist.stem!s}.tgz {playlist!s} {playlist!s}',
            )
            done()
        player.add_skips(skip)

        # Run the player {{{2
        first = True
        songs_already_played = []
        while first or repeat:
            if shuffle:
                narrate('shuffling')
                player.shuffle_songs()
            narrate('playing songs ...')
            loop = GLib.MainLoop()
            thread = threading.Thread(
                target=player.play,
                args=(loop.quit, args['--terse'])
            )
            thread.setDaemon(True)
            thread.start()
            loop.run()
            first = False
            if repeat:
                display("rewinding")
    except KeyboardInterrupt:
        display('mp: killed at user request.')
        songs_already_played = player.songs_already_played()
    except Error as e:
        e.terminate()

    # Termination {{{2
    if now_playing_path:
        try:
            now_playing_path.unlink()
        except FileNotFoundError:
            pass

    # write out restart information
    if write_restart_file:
        try:
            narrate('writing:', restart_path)
            restart_path.write_text('\n'.join(
                str(l)
                for l in cmd_line[1:] + [separator] + songs_already_played
            ) + '\n')
        except OSError as e:
            error(os_error(e))

    # we are done here
    done()
