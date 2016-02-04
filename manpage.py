#!/usr/bin/env python

# MP Documentation
#
# Converts a restructured text version of the manpages to nroff.

# License {{{1
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
# along with this program.  If not, see http://www.gnu.org/licenses/.

# Imports {{{1
from inform import conjoin
from music_player import mediaFileExtensions, version, date
from textwrap import dedent
from docutils.core import publish_string
from docutils.writers import manpage

# Program Manpage {{{1
PROGRAM_MANPAGE = {
    'name': 'mp',
    'sect': '1',
    'contents': r"""{
        ====
         mp
        ====

        ------------
        music player
        ------------

        :Author: Ken Kundert <mp@nurdletech.com>
        :Date: {date}
        :Version: {version}
        :Manual section: 1

        .. :Copyright: public domain
        .. :Manual group: Multimedia

        SYNOPSIS
        ========
        mp [ options ] args ...

        DESCRIPTION
        ===========
        ``mp`` plays any music files given on its command line. If either a play list
        (m3u file) or a  directory is given, it will be recursively searched
        for music files, which will be added to the list of songs to be
        played.

        Currently only {extensions} music files and simple .m3u play lists are 
        supported.

        Use Ctrl-Z to pause and 'fg' to continue. Use Ctrl-C when running to kill.

        OPTIONS
        =======

        -q, --quiet     Do not print name of the music file being played.
        -r, --repeat    Repeat songs.
        -s, --shuffle   Shuffle songs.  If combined with repeat, the songs will be
                        shuffled before each repeat.
        -p <filename.m3u>, --playlist <filename.m3u>
                        Generate a playlist from the music specified rather than play
                        the music.

        If invoked with no arguments or options ``mp`` will repeat the session that was 
        previously run in the same directory, skipping any songs that had already been 
        played.

        The artist and title of the currently playing song is available from 
        ~/.nowplaying.

        If you would like to be able to control the music player from the 
        keyboard without direct access to the program, consider binding keys to 
        the following commands:
        
        ======== ============= ========================
        Action   Suggested Key Command
        ======== ============= ========================
        pause    XF86AudioStop killall -STOP mp
        continue XF86AudioPlay killall -CONT mp
        start                  cd ~/media/music && mp &
        stop                   killall -INT mp
        ======== ============= ========================

        This assumes that you have your music stored in ~/media/music and that 
        you cd to that directory initially and run mp with your choice of music 
        files and settings. Once you have done that you control mp remotely 
        with the above commands.

        A simple way to listen to your favorite music is to cd to you music 
        directory and run ``mp -p favorites.m3u *``, then edit that file and 
        delete any songs you not interested in hearing. Then run 'mp -r -s 
        favorite.m3u'. Or, if that results is a file that is just too big to 
        manage easily, you can do the same in each of the subdirectories, and 
        then run ``mp -r -s */favorites.m3u`` to play your music.

    }"""
}

# Generate restructured text {{{1
def write(genRST=False):
    for each in [PROGRAM_MANPAGE]:
        rst = dedent(each['contents'][1:-1]).format(
            date=date
          , version=version
          , extensions=conjoin(mediaFileExtensions, conj=" and ", sep=", ")
        )

        # generate reStructuredText file (only used for debugging)
        if genRST:
            print("generating %s.%s.rst" % (each['name'], each['sect']))
            with open('%s.%s.rst' % (each['name'], each['sect']), 'w') as f:
                f.write(rst)

        # Generate man page
        print("generating %s.%s" % (each['name'], each['sect']))
        with open('%s.%s' % (each['name'], each['sect']), 'w') as f:
            f.write(publish_string(rst, writer=manpage.Writer()).decode())

if __name__ == '__main__':
    write(True)

# vim: set sw=4 sts=4 formatoptions=ntcqwa12 et spell:
