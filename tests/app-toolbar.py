#!/usr/bin/env python2.4

from eagle import *

def callback():
    info( "toolbar item clicked" )

App( title="Test Toolbar",
     toolbar=(("Test", "test.png", "test this toolbar item", callback ),
              "---------",
              ("Test", "test.png", "test this toolbar item", callback ),
              ),
     )

run()
