from distutils.core import setup
import manpage # importing manpage has the side effect of creating nroff version

longDescription='''
Music player.
'''

setup(
    name='mp'
  , version='1.0'
  , description='music player'
  , long_description=longDescription
  , author="Ken Kundert"
  , author_email='mp@shalmirane.com'
  , scripts=['mp']
  , py_modules=['mp', 'config', 'cmdline', 'fileutils', 'kskutils']
  , data_files=[
        ('man/man1', ['mp.1'])
    ]
  , platforms=['rhel']
)
