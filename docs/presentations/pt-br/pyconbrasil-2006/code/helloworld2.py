#!/usr/bin/env python

from eagle import *

def my_func( app, button ):
	print "app=%s, button=%s" % ( app, button )

App( title="Hello World!",
     center=Button( id="btn",
                    label="Hello World!",
		    callback=my_func ) )

run()
