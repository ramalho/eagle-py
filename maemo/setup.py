 #!/usr/bin/env python2

import os
import sys
sys.path.append( ".." )

try:
    import eagle_setup
except ImportError, e:
    a = os.path.split( sys.argv[ 0 ] )
    module = os.path.join( *a[ : -1 ] )
    script = a[ -1 ]
    python = sys.executable
    sys.stderr.writelines(
        ( "You should run this file from inside module subdirectory.\n",
          "\tcd %s; %s %s\n" % ( module, python, script ),
          ) )
    sys.exit( -1 )

from eagle_setup import recursive_data_files

eagle_setup.setup( "maemo",
                   install_requires=[ "pygtk>=2.6" ],
                   data_files=recursive_data_files( "share", "*" ),
                   )
