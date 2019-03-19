# Music Player Settings

from pathlib import Path

media_file_extensions = ['.flac', '.mp3', '.ogg', '.wav'] # use lower case only
restart_path = Path('.mp-restart').expanduser()
now_playing_path = Path('~/.nowplaying').expanduser()
separator = '### skip the following songs ###'
skip_song_that_was_playing_when_last_killed = True
