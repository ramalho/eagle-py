#!/usr/bin/python

import pygst
pygst.require("0.10")

import gst
from eagle import *

class Player(object):
    STATE_STOPPED = gst.STATE_NULL
    STATE_READY = gst.STATE_READY
    STATE_PAUSED = gst.STATE_PAUSED
    STATE_PLAYING = gst.STATE_PLAYING

    def __init__(self, callback=None):
        self.is_playing = False
        self.filename = None

        self.bin = gst.parse_launch("playbin")
        self.bus = self.bin.get_bus()
        self.bus.enable_sync_message_emission()
        self.bus.add_signal_watch()

        if callback:
            def on_message(bus, message):
                t = message.type
                if   t == gst.MESSAGE_EOS:
                    self.is_playing = False
                    self.filename = None
                    callback(self)
                elif t == gst.MESSAGE_ERROR:
                    err, debug = message.parse_error()
                    print "Error: %s" % err, debug
            self.bus.connect("message", on_message)


    def play(self, filename):
        self.bin.set_property("uri", "file://%s" % filename)
        self.bin.set_state(gst.STATE_PLAYING)
        self.filename = filename
        self.is_playing = True


    def stop(self):
        self.bin.set_state(gst.STATE_NULL)
        self.bin.set_property("uri", "")
        self.filename = None
        self.is_playing = False


    def pause(self):
        if self.is_playing:
            self.bin.set_state(gst.STATE_PAUSED)
        else:
            self.bin.set_state(gst.STATE_PLAYING)

        self.is_playing = not self.is_playing


def add_file(app, button, value):
    app["playlist"].append(value)


def play(app, button):
    rows = app["playlist"].selected()
    if rows:
        idx, row = rows[0]
        fname = row[0]
        app["play"].set_inactive()
        app.player.stop()
        app.player.play(fname)
        app["play"].set_inactive()
        app["pause"].set_active()
        app["stop"].set_active()
        app["now_playing"] = "Playing %s" % app.player.filename


def pause(app, button):
    app.player.pause()
    if app.player.is_playing:
        msg = "Playing %s" % app.player.filename
        app["play"].set_inactive()
        app["pause"].set_active()
        app["stop"].set_active()
    else:
        msg = "Paused %s" % app.player.filename
        app["play"].set_inactive()
        app["pause"].set_active()
        app["stop"].set_active()
    app["now_playing"] = msg


def stop(app, button):
    app.player.stop()
    app["play"].set_active(bool(app["playlist"].selected()))
    app["pause"].set_inactive()
    app["stop"].set_inactive()
    app["now_playing"] = "Nothing is playing!"


def playlist_selected(app, table, rows):
    if rows:
        app["play"].set_active()


def end_of_stream(player):
    app = get_app_by_id("music_player")
    app["play"].set_active(bool(app["playlist"].selected()))
    app["pause"].set_inactive()
    app["stop"].set_inactive()
    app["now_playing"] = "Nothing is playing!"


app = App(id="music_player",
          title="Music Player",
          top=(OpenFileButton(id="add_file",
                              filter=("*.mp3", "*.ogg"),
                              callback=add_file,
                              ),
               ),
          center=(Table(id="playlist",
                        label=None,
                        show_headers=False,
                        types=(str,),
                        selection_callback=playlist_selected,
                        ),
                  ),
          bottom=(Button(id="play",
                         stock="media:play",
                         callback=play,
                         ),
                  Button(id="pause",
                         stock="media:pause",
                         callback=pause,
                         ),
                  Button(id="stop",
                         stock="media:stop",
                         callback=stop,
                         ),
                  Label(id="now_playing",
                        label="Nothing is Playing!",
                        ),
                  )
          )

app.player = Player(callback=end_of_stream)
app["play"].set_inactive()
app["pause"].set_inactive()
app["stop"].set_inactive()


run()
