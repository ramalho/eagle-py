#!/usr/bin/env python2

from eagle import *

def callback( app, entry, value ):
    print app, entry, value

App( title="Slider test",
     left=Slider( id="hslider",
                  label="Slider:",
                  value_pos=Slider.POS_NONE,
                  horizontal=True,
                  min=0, max=10,
                  callback=callback ),
     right=Slider( id="vslider",
                   label=None,
                   horizontal=False,
                   value_pos=Slider.POS_LEFT,
                   min=0, max=100,
                   callback=callback,
                   expand_policy=ExpandPolicy.All()),
     )

run()
