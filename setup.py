from setuptools import setup
import manpage # importing manpage has the side effect of creating nroff version

longDescription='''
Simple music player.
'''

setup(
    name='mp'
  , version='1.0'
  , description='music player'
  , long_description=longDescription
  , author="Ken Kundert"
  , author_email='mp@nurdletech.com'
  , scripts=['mp']
  , py_modules=['mp', 'config', 'cmdline', 'fileutils', 'kskutils']
  , data_files=[
        ('man/man1', ['mp.1'])
    ]
  , platforms=['rhel']
  , use_2to3=True
  , license='GPLv3'
)
