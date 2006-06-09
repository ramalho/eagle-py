#!/usr/bin/python

import gst
from eagle import *

class Player( object ):
    STATE_STOPPED = gst.STATE_NULL
    STATE_READY = gst.STATE_READY
    STATE_PAUSED = gst.STATE_PAUSED
    STATE_PLAYING = gst.STATE_PLAYING

    def __init__( self, callback=None ):
        self.bin = gst.parse_launch( "playbin" )
        if callback:
            def state_changed( bin, old, new ):
                callback( self, new )
            # state_changed()
            self.bin.connect( "state-change", state_changed )

            def eos( bin ):
                callback( self, self.STATE_STOPPED )
            # eos()
            self.bin.connect( "eos", eos )
        self.filename = None
    # __init__()


    def play( self, filename ):
        self.filename = filename
        self.bin.props.uri = "file://%s" % filename
        self.bin.set_state( gst.STATE_PLAYING )
    # play()


    def stop( self ):
        self.bin.set_state( gst.STATE_NULL )
        self.filename = None
    # stop()


    def is_playing( self ):
        return self.bin.get_state() == gst.STATE_PLAYING
    # is_playing()


    def pause( self ):
        if self.is_playing():
            self.bin.set_state( gst.STATE_PAUSED )
        else:
            self.bin.set_state( gst.STATE_PLAYING )
    # pause()
# Player


def add_file( app, button, value ):
    app[ "playlist" ].append( value )
# add_file()


def play( app, button ):
    rows = app[ "playlist" ].selected()
    if rows:
        idx, row = rows[ 0 ]
        fname = row[ 0 ]
        app[ "play" ].set_inactive()
        app.player.stop()
        app.player.play( fname )
# play()


def pause( app, button ):
    app.player.pause()
# pause()


def stop( app, button ):
    app.player.stop()
    app[ "play" ].set_active( bool( app[ "playlist" ].selected() ) )
# stop()


def playlist_selected( app, table, rows ):
    if rows:
        app[ "play" ].set_active()
# playlist_selected()


def player_state_changed( player, state ):
    app = get_app_by_id( "music_player" )
    msg = ""
    if state == player.STATE_PLAYING:
        msg = "Playing %s" % player.filename
        app[ "pause" ].set_active()
        app[ "stop" ].set_active()
    elif state == player.STATE_PAUSED:
        msg = "Paused %s" % player.filename
    else:
        msg = "Nothing is Playing!"
        app[ "pause" ].set_inactive()
        app[ "stop" ].set_inactive()

    app[ "now_playing" ] = msg
# player_state_changed()


app = App( id="music_player",
           title="Music Player",
           top=( OpenFileButton( id="add_file",
                                 filter=( "*.mp3", "*.ogg" ),
                                 callback=add_file,
                                 ),
                 ),
           center=( Table( id="playlist",
                           label=None,
                           show_headers=False,
                           types=( str, ),
                           selection_callback=playlist_selected,
                           ),
                    ),
           bottom=( Button( id="play",
                            stock="media:play",
                            callback=play,
                            ),
                    Button( id="pause",
                            stock="media:pause",
                            callback=pause,
                            ),
                    Button( id="stop",
                            stock="media:stop",
                            callback=stop,
                            ),
                    Label( id="now_playing",
                           label="Nothing is Playing!",
                           ),
                    )
           )

app.player = Player( callback=player_state_changed )
app[ "play" ].set_inactive()
app[ "pause" ].set_inactive()
app[ "stop" ].set_inactive()


run()
