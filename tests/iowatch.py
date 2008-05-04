#!/usr/bin/env python2

from eagle import *
import os

rfd, wfd = os.pipe()

def add_data(app, button):
    os.write(wfd, "data\n")
# add_data()

def io_watch_read(app, fileobj, **kargs):
    print "io event:", app, fileobj, kargs
    v = app["entry"]
    txt = []
    while True:
        c = os.read(fileobj, 1)
        txt.append(c)
        if c == '\n':
            break

    v += "".join(txt)
    app["entry"] = v

    return True
# io_watch_read()


event_id = None


def start(app, button):
    global event_id
    event_id = app.io_watch(rfd, io_watch_read, on_in=True)
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


app = App(title="I/O watch example",
          center=(Entry(id="entry",
                        label="Data Read",
                        multiline=True,
                        ),
                  ),
          right=(Button(id="generate",
                        label="Generate Data",
                        callback=add_data),
                 HSeparator(),
                 Button(id="start",
                        label="start",
                        callback=start,
                        ),
                 Button(id="stop",
                        stock="stop",
                        callback=stop,
                        ),
                 ),
          )

app["stop"].set_inactive()

run()
