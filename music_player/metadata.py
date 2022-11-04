# MetaData class
#
# Used to access the music file metadata (title, artist, etc.).

# Imports {{{1
from inform import Color, join, os_error, warn
from .prefs import (
    show_album, show_track,
    title_color, artist_color, album_color, path_color, punct_color
)
title_color = Color(title_color, Color.isTTY())
artist_color = Color(artist_color, Color.isTTY())
album_color = Color(album_color, Color.isTTY())
path_color = Color(path_color, Color.isTTY())
punct_color = Color(punct_color, Color.isTTY())

# MetaData constructor {{{1
# I have a very weak understanding of the way metadata is implemented and why
# this is so hard.
class MetaData(object):
    def __init__(self, media_path, now_playing_path):
        self.media_path = media_path
        media_filename = str(media_path)
        self.now_playing_path = now_playing_path
        self.artist = None
        self.album = None
        self.title = None
        self.track = None
        self.volume = None
        self.warned = False

        # Try EasyID3 metadata
        try:
            from mutagen.easyid3 import EasyID3
            from mutagen import MutagenError
            try:
                metadata = EasyID3(media_filename)
                self._get_easy_metadata(metadata)
                return
            except MutagenError:
                pass
        except ImportError:
            pass

        # If that did not work, try ID3 metadata
        try:
            from mutagen.id3 import ID3, ID3NoHeaderError
            try:
                metadata = ID3(media_filename)
                self._get_id3_metadata(metadata)
                return
            except ID3NoHeaderError:
                pass
        except ImportError:
            pass

        # If those did not work, filetype specific metadata
        ext = media_path.suffix.lower()
        if ext in ['.ogg', 'oga']:
            try:
                from mutagen.oggvorbis import OggVorbis, OggVorbisHeaderError
                try:
                    metadata = OggVorbis(media_filename)
                    self._get_easy_metadata(metadata)
                    return
                except OggVorbisHeaderError:
                    pass
            except ImportError:
                pass
        elif ext == '.mp3':
            try:
                from mutagen.mp3 import MP3, HeaderNotFoundError
                try:
                    metadata = MP3(media_filename)
                    self._get_id3_metadata(metadata)
                    return
                except HeaderNotFoundError:
                    pass
            except ImportError:
                pass
        elif ext == '.flac':
            try:
                from mutagen.flac import FLAC, FLACNoHeaderError
                try:
                    metadata = FLAC(media_filename)
                    self._get_easy_metadata(metadata)
                    return
                except FLACNoHeaderError:
                    pass
            except ImportError:
                pass
        # if we get here we failed to get the metadata

    # summary() {{{1
    def summary(self):
        if self.album:
            album = join(
                album = self.album if show_album else None,
                track = self.track.lstrip('0') if self.track and show_track else None,
                volume = self.volume if show_track else None,
                template = (
                    '{album} (vol {volume}, track {track})',
                    '{album} (track {track})',
                    '{album}',
                    '',
                )
            )
        else:
            album = None
        return join(
            artist = artist_color(self.artist) if self.artist else None,
            title = title_color(self.title) if self.title else None,
            path = path_color(self.media_path) if self.media_path else None,
            sep = punct_color('—'),
            album = album_color(album) if album else None,
            template = (
                '{title} {sep} {artist} {sep} {album}',
                '{title} {sep} {artist}',
                '{title} {sep} {album}',
                '{title}',
                '{path}',
            )
        )

    # now_playing() {{{1
    def now_playing(self):
        if self.now_playing_path:
            out = [each for each in [self.artist, self.title] if each]
            try:
                self.now_playing_path.write_text(' — '.join(out))
            except OSError as e:
                if not self.warned:
                    warn(os_error(e))
                    self.warned = True

    # _get_easy_metadata() (private) {{{1
    def _get_easy_metadata(self, metadata):
        self.artist = metadata.get('artist', [None])[0]
        self.album = metadata.get('album', [None])[0]
        self.title = metadata.get('title', [None])[0]
        self.track = metadata.get('tracknumber', [None])[0]
        self.volume = metadata.get('discnumber', [None])[0]

    # _get_id3_metadata() (private) {{{1
    def _get_id3_metadata(self, metadata):
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
