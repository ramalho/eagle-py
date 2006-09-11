#!/usr/bin/env python2

from eagle import *

App(title="Test of buttons with images",
    center=(Button(id="b0",
                   label="my label",
                   image="test.png"),
            Button(id="b1",
                   label="my label",
                   image=Image(filename="test.png")),
            Button(id="b2",
                   label=None,
                   image="test.png")))

run()
