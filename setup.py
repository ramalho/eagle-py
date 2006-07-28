#!/usr/bin/env python2

__author__ = "Gustavo Sverzut Barbieri"
__author_email__ = "barbieri@gmail.com"
__license__ = "LGPL"
__url__ = "http://www.gustavobarbieri.com.br/eagle/"
__version__ = "0.7"
__revision__ = "$Rev: 20 $"
__description__ = """\
Eagle is an abstraction layer atop Graphical Toolkits focused on making simple applications easy to build while powerful in features.
"""
__long_description__ = """\
Eagle is an abstraction layer atop Graphical Toolkits focused on
making simple applications easy to build while powerful in features.

With Eagle you have many facilities to build application that needs
just some buttons, user input and a canvas to draw.

Canvas is really simple, what makes Eagle a great solution to
Computer Graphics and Image Processing software, the primary focus
of this library.

User input widgets are persistent, you just need to mark them
"persistent" or put them in the preferences area.

Eagle is not meant to be another Graphical Toolkit, you already
have a bunch of them, like Qt, Gtk, wxWidgets (to name just a few).
It's focused on applications that have few windows, with buttons,
simple user input and canvas. Widgets are laid out automatically
in 5 areas: left, right, top, bottom and center.

It provides useful widgets like: Color selector, Font selector,
Quit button, Preferences button and bialog, About dialog and Help
dialog.
"""

import os
import sys
from glob import glob
import ez_setup
ez_setup.use_setuptools()

import setuptools

pjoin = os.path.join


blacklist_start = [ "." ]
blacklist_end   = [ "~", ".pyc", ".pyo" ]

def listfiles( *args ):
    p = pjoin( *args )
    files = glob( p )
    r = []
    for f in files:
        if os.path.isfile( f ):
            fname = os.path.basename( f )
            for b in blacklist_start:
                if fname.startswith( b ):
                    break
            else:
                for b in blacklist_end:
                    if fname.endswith( b ):
                        break
                else:
                    r.append( f )
    return r


def recursive_data_files( *args ):
    files = listfiles( *args )

    dirname = list( args[ : -1 ] or [ "." ] )
    d = pjoin( *dirname )

    ret = [ ( d, files ) ]

    try:
        l = os.listdir( d )
    except OSError, e:
        return []

    for f in l:
        if f.startswith( "." ):
            continue

        fp = pjoin( d, f )
        if os.path.isdir( fp ):
            a = dirname + [ f, args[ -1 ] ]
            ret.extend( recursive_data_files( *a ) )

    return ret


def setup( module, install_requires=None, data_files=None ):
    data_files = list( data_files or [] )
    data_files += [
        ( "tests", listfiles( "tests", "*" ) ),
        ( "examples", listfiles( "examples", "*" ) ),
        ]
    data_files += recursive_data_files( module, "share", "*" )

    docs = recursive_data_files( "docs", "*" )
    for i, ( d, f ) in enumerate( docs ):
        docs[ i ] = ( d, f )

    data_files += docs

    # prefix data_files with share/python2.4-maemo/
    pkg = "python%s.%s-eagle" % ( sys.version_info[ 0 ],
                                  sys.version_info[ 1 ] )
    prefix = "share/%s" % pkg
    doc_prefix = "share/doc/%s" % pkg
    tmp = []
    doc = "docs"
    module_doc = pjoin( module, "share", "docs" )
    for ( a, b ) in data_files:
        if a.startswith( doc ):
            p = pjoin( doc_prefix, a[ len( doc ) + 1 : ] )
        elif a.startswith( module_doc ):
            p = pjoin( doc_prefix, a[ len( module_doc ) + 1 : ] )
        else:
            p = pjoin( prefix, a )

        if b:
            tmp.append( ( p, b ) )
    data_files = tmp


    return setuptools \
           .setup( name=("eagle-%s" % module),
                   py_modules=[ "eagle" ],
                   package_dir = { '': module },
                   include_package_data=True,
                   data_files=data_files,
                   install_requires=install_requires,
                   version=__version__,
                   description=__description__,
                   long_description=__long_description__,
                   url=__url__,
                   license=__license__,
                   author=__author__,
                   author_email=__author_email__,
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

cwd = os.path.basename( os.getcwd() ).split( '-' )

if len( cwd ) > 1:
    module = cwd[ 1 ]
else:
    module = None


if __name__ == "__main__":
    ## Enable module based on directory name:
    # eagle-MODULE[-version] will build just MODULE
    # if MODULE is missing, build everything
    if not module or module == "gtk":
        setup( "gtk", [] )

    if not module or module == "maemo":
        setup( "maemo", [] )
