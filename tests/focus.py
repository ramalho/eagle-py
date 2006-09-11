#!/usr/bin/env python2

from eagle import *

def focus_e0( app, button ):
    app.get_widget_by_id( "e0" ).focus()

def focus_e1( app, button ):
    app.get_widget_by_id( "e1" ).focus()

def focus_b0( app, button ):
    app[ "b0" ].focus()


App( title="Test focus",
     top=( Button( id="b0",
                   label="Focus e0",
                   callback=focus_e0,
                   ),
           Button( id="b1",
                   label="Focus e1",
                   callback=focus_e1,
                   ),
           Button( id="b2",
                   label="Focus b0",
                   callback=focus_b0,
                   ),
           ),
     center=( Entry( id="e0",
                     label="e0",
                     ),
              Entry( id="e1",
                     label="e1",
                     ),
              )
     )

run()
