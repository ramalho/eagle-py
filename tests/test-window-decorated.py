#!/usr/bin/env python2

from eagle import App, CheckBox, run

def toggle_decoration(app, cb, value):
    app.window_decorated = value


App(title="Change Window Decoration",
    window_decorated=False,
    center=CheckBox(id="cb",
                    label="Window is decorated",
                    callback=toggle_decoration,
                    ),
    )
run()
