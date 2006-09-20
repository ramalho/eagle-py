#!/usr/bin/env python2

from eagle import *


app = App( title="Test hidden image drawing",
           center=Tabs( id="t0",
                        children=( Tabs.Page( label="tab1",
                                              children=Canvas( id="c0",
                                                               width=200,
                                                               height=200,
                                                               bgcolor="white",
                                                               )
                                              ),
                                   Tabs.Page( label="tab2",
                                              children=Canvas( id="c1",
                                                               width=200,
                                                               height=200,
                                                               bgcolor="white",
                                                               )
                                              ),
                                   )
                        )
           )

img = Image( filename="test.png" )
app[ "c0" ].draw_image( img )
app[ "c1" ].draw_image( img )
app[ "c0" ].draw_text( "Hello" )
app[ "c1" ].draw_text( "World" )

run()
