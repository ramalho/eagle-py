#!/usr/bin/env python2

from eagle import App, UIntSpin, run

def fill_window_size( app ):
    width, height = app.window_size
    app["width"] = width
    app["height"] = height

def set_window_size( app, *ignored ):
    width = app["width"]
    height = app["height"]
    if width and height:
        app.window_size = ( width, height )


app = App(title="Test Window Size",
          window_size=( 400, 400 ),
          center=(UIntSpin(id="width",
                           label="Width:",
                           callback=set_window_size,
                           ),
                  UIntSpin(id="height",
                           label="Height:",
                           callback=set_window_size,
                           ),
                  )
          )

app.idle_add( fill_window_size )


run()
