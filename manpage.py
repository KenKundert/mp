#!/bin/env python
# Convert the restructured text version of the manpage to a nroff manpage file.

from kskutils import conjoin
from config import mediaFileExtensions, version, date
#from datetime import date as Date
from docutils.core import publish_string
from docutils.writers import manpage

#date = Date.today()
with open('mp.rst') as inputFile:
    text = inputFile.read().format(
        date=date
      , version=version
      , extensions=conjoin(mediaFileExtensions, conj=" and ", sep=", ")
    )
    with open('mp.1', 'w') as outputFile:
        outputFile.write(
            publish_string(text, writer=manpage.Writer())
        )
