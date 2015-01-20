#!/usr/bin/env python

# Global configuration settings
mediaFileExtensions = ['.flac', '.mp3', '.ogg', '.wav'] # use lower case only
assert 'm3u' not in mediaFileExtensions
restartFilename = '.mp-restart'
separator = '### skip the following songs ###'
version = "1.2"
date = "2015-01-17"
skipSongThatWasPlayingWhenLastKilled = False
