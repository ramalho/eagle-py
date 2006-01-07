#!/usr/bin/env python2

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

import eagle

setup( name="eagle",
       py_modules=[ "eagle" ],
       package_dir = { '': '.' },
       include_package_data=True,
##        data_files=[
##     ( pjoin( "share", "tests" ), listfiles( "tests", "*" ) ),
##     ],
       install_requires=[ "pygtk>=2.6" ],
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

