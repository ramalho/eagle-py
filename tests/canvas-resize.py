#!/usr/bin/env python2

from eagle import *

def resize_canvas(app, canvas, width, height):
    canvas.resize(width, height)
    canvas.clear()
    canvas.draw_text("size: %dx%d" % (width, height), fgcolor="white")

App(title="Resize Canvas",
    center=Canvas(id="c0",
                  label=None,
                  scrollbars=None,
                  width=200,
                  height=300,
                  resize_callback=resize_canvas,
                  ),
    )

run()
