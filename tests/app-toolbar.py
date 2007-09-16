#!/usr/bin/env python2.4

from eagle import *

def callback( app, toolbar_item):
    info( "clicked on toolbar item %s of %s" % ( toolbar_item, app ) )

App( title="Test Toolbar",
     toolbar=(Toolbar.Item( label="Test",
                            image="test.png",
                            tooltip="test this toolbar item",
                            callback=callback ),
              Toolbar.Separator(),
              Toolbar.Item( label="Test",
                            image="test.png",
                            tooltip="test this toolbar item",
                            callback=callback,
                            active=False ),
              Toolbar.Item( stock="open", callback=callback ),
              ),
     )

run()
