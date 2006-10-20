#!/usr/bin/env python2.4

from eagle import *

def callback( app, toolbar_item):
    info( "clicked on toolbar item %s of %s" % ( toolbar_item, app ) )

App( title="Test Toolbar",
     toolbar=(App.Toolbar.Item( "Test",
                                "test.png",
                                "test this toolbar item",
                                callback ),
              App.Toolbar.Separator(),
              App.Toolbar.Item( "Test",
                                "test.png",
                                "test this toolbar item",
                                callback,
                                active=False ),
              ),
     )

run()
