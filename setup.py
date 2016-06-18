from setuptools import setup
from music_player import version

# Create/update manpage before installing
message = ''
try:
    import manpage
    manpage.write()  # generate the nroff version of the manpage
except ImportError:
    # this will let the setup script run, allowing prerequisites to be 
    # installed, but then setup script must be run again so manpage is 
    # generated.
    with open('mp.1', 'w') as f:
        f.write('')
    message='\nRerun setup in order to generate the manpage.'

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
  , license='GPLv3+'
  , install_requires=[
        'mutagen',
        'gi',
    ],
    # there seems to be a problem with the python3 version of gi. If you allow
    # python to install gi itself, it seems to pick up the python2 version. So
    # instead, you should remove it from the list above and use the system's
    # package manager to install gi. For example, on Fedora23 use:
    #     dnf install python3-gobject
)

print(message)
