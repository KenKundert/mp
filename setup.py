from setuptools import setup

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
    longDescription = f.read()

setup(
    name = 'mp',
    version = '1.7.0',
    description = 'simple music player',
    long_description = longDescription,
    author = "Ken Kundert",
    author_email = 'mp@nurdletech.com',
    scripts = ['mp'],
    packages = ['music_player'],
    data_files = [
        ('man/man1', ['mp.1'])
    ],
    zip_save = True,
    license = 'GPLv3+',
    install_requires = [
        'appdirs',
        'docopt',
        'inform>=1.22',
        'mutagen',
        'pygobject',
    ],
    python_requires = '>=3.6',
)

print(message)
