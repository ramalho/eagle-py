#!/usr/bin/env python2

from eagle import App, Entry, run

def change_title(app, entry, value):
    app.title = value

App(title="Change this title",
    center=Entry(id="e0",
                 label="New title:",
                 callback=change_title)
    )

run()
