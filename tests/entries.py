#!/usr/bin/env python2

from eagle import *

def changed( app, entry, value ):
    print "app %s, entry %s, value %r" % ( app.id, entry.id, value )
# changed()


App( title="Entries Test",
     center=( Entry( id="single" ),
              Entry( id="multi", multiline=True ),
              ),
     data_changed_callback=changed,
     )

run()
