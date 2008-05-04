#!/usr/bin/env python2

from eagle import *
import time

def showtime(app):
    app["time"] = time.asctime()
    return True
# showtime()

event_id = None

def start(app, button):
    global event_id
    event_id = app.timeout_add(100, showtime)
    button.set_inactive()
    app["stop"].set_active()
# start()


def stop(app, button):
    global event_id
    app.remove_event_source(event_id)
    event_id = None
    button.set_inactive()
    app["start"].set_active()
# stop()


app = App(title="timer example",
          center=(Label(id="time"),
                  ),
          right=(Button(id="stop",
                        stock="stop",
                        callback=stop,
                        ),
                 Button(id="start",
                        label="start",
                        callback=start,
                        ),
                 ),
          )
app["stop"].set_inactive()

run()
