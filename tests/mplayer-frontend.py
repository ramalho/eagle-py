#!/usr/bin/env python2

from eagle import *
import subprocess
import os
import signal
import time


def player_stop(app):
    if app.playing:
        os.kill(app.playing.pid, signal.SIGTERM)
        time.sleep(1) # XXX should do proper finalization and wait for SIGCHLD
        app.playing = None

def player_start(app, filename):
    # XXX real world would use -slave option and controls using stdin/stdout
    xid = app["slot"].get_resource()
    cmd = "mplayer -wid %#x %r" % (xid, filename)
    app["cmd"] = cmd
    app.playing = subprocess.Popen(cmd, shell=True)

def stop_clicked(app, widget):
    player_stop(app)

def file_selected(app, widget, filename):
    player_stop(app)
    player_start(app, filename)

app = App(title="MPlayer Front End",
          top=(OpenFileButton(callback=file_selected),
               Button(id="stop", stock="media:stop", callback=stop_clicked),
               ),
          center=(Entry(id="cmd", label="Command", editable=False),
                  NativeSlot(id="slot"),
                  )
          )
app.playing = None

run()

player_stop(app)
