#!/usr/bin/env python2

from eagle import *

data = chr(128) * ( 30 * 30 * 3 )
img = Image( width=30, height=30, depth=24,
             data=data)

def change_b3( app, button ):
    if button.image == "test.png":
        button.image = img
    else:
        button.image = "test.png"


App( title="Test of buttons with images",
     center=( Button( id="b0",
                      label="my label",
                      image="test.png",
                      ),
              Button( id="b1",
                      label="my label",
                      image=Image( filename="test.png" ),
                      ),
              Button( id="b2",
                      label=None,
                      image="test.png",
                      ),
              Button( id="b3",
                      label="Change-me",
                      image="test.png",
                      callback=change_b3,
                      ),
              )
     )

run()
