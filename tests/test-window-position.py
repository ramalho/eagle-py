#!/usr/bin/env python2

from eagle import App, UIntSpin, Button, get_desktop_size, run

def fill_window_position( app ):
    x, y = app.window_position
    app["x"] = x
    app["y"] = y

def set_window_position( app, *ignored ):
    x = app["x"]
    y = app["y"]
    if x and y:
        app.window_position = ( x, y )

def center_window( app, button ):
    w, h = app.window_size
    dw, dh = get_desktop_size()
    x = ( dw - w ) / 2
    y = ( dh - h ) / 2
    app.window_position = ( x, y )


app = App(title="Test Window Position",
          window_position=( 400, 400 ),
          center=(UIntSpin(id="x",
                           label="X:",
                           callback=set_window_position,
                           ),
                  UIntSpin(id="y",
                           label="Y:",
                           callback=set_window_position,
                           ),
                  Button(id="center",
                         label="Center",
                         callback=center_window,
                         ),
                  )
          )

app.idle_add( fill_window_position )


run()
