from setuptools import setup
import manpage
from music_player import version
manpage.write()  # generate the nroff version of the manpage

with open('README.rst') as f:
    longDescription=f.read()

setup(
    name='mp'
  , version=version
  , description='simple music player'
  , long_description=longDescription
  , author="Ken Kundert"
  , author_email='mp@nurdletech.com'
  , scripts=['mp']
  , packages=['music_player', 'scripts']
  , data_files=[
        ('man/man1', ['mp.1'])
    ]
  , platforms=['rhel']
  , use_2to3=True
  , license='GPLv3'
)
