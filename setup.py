#!/usr/bin/env python2

from distutils.core import setup

import eagle
import os
from fnmatch import fnmatch

blacklisted_file_patterns = ( "*~", "*.pyc", "*.pyo" )

def is_blacklisted( filename ):
    for p in blacklisted_file_patterns:
        if fnmatch( filename, p ):
            return True
    return False
# is_blacklisted()

def listfiles( *dirs ):
    dir, pattern = os.path.split( os.path.join( *dirs ) )
    return [os.path.join( dir, filename )
            for filename in os.listdir( os.path.abspath( dir ) )
            if filename[ 0 ] != '.' and fnmatch( filename, pattern ) and \
            not is_blacklisted( filename ) ]
# listfiles()

pjoin = os.path.join

setup( name="eagle",
       py_modules=[ "eagle" ],
       data_files=[
    ( pjoin( "share", "tests" ), listfiles( "tests", "*" ) ),
    ],
       version=eagle.__version__,
       description=eagle.__description__,
       long_description=eagle.__long_description__,
       url=eagle.__url__,
       license=eagle.__license__,
       author=eagle.__author__,
       author_email=eagle.__author_email__,
       classifiers=[
    "Development Status :: 5 - Production/Stable",
    "Environment :: X11 Applications",
    "Environment :: Win32 (MS Windows)",
    "Environment :: MacOS X",
    "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    ]
       )

