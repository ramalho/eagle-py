#!/usr/bin/env python

from eagle import *
import re
import time
import webbrowser
import socket
import struct


class Chat( object ):
    def __init__( self, host, port, app, callback ):
        self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.conn = None
        self.app = app
        self.callback = callback
        self.cb_id = None

        self.client_mode = self.connect( host, port )
        if not self.client_mode:
            self.serve( port )
    # __init__()


    def __setup_callback__( self ):
        self.cb_id = self.app.io_watch( self.conn, self.callback, on_in=True,
                                        on_error=True, on_hungup=True )
    # __setup_callback__()


    def __remove_callback__( self ):
        if self.cb_id:
            self.app.remove_event_source( self.cb_id )
    # __remove_callback__()


    def disconnect( self ):
        if self.cb_id is not None:
            self.app.remove_event_source( self.cb_id )
        self.sock.close()

    def connect( self, host, port ):
        try:
            self.sock.connect( ( host, port ) )
            self.conn = self.sock
            self.__setup_callback__()
            return True
        except socket.error, e:
            self.__remove_callback__()
            print "could not connect to server at %s:%s: %s" % \
                  ( host, port, e )
            return False
    # connect()


    def accept_connection(self, app, sock, *ign, **kign ):
        conn, address = sock.accept()
        if conn:
            self.conn = conn
            self.__setup_callback__()
        else:
            self.__remove_callback__()
        return False
    # accept_connection()


    def serve( self, port ):
        self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.sock.bind( ( "", port ) )
        self.sock.listen( 5 )
        self.app.io_watch( self.sock, self.accept_connection, on_in=True )
    # serve()


    def read( self ):
        try:
            size_bin = self.conn.recv( struct.calcsize( "!l" ) )
            size = struct.unpack( "!l", size_bin )[ 0 ]
            return self.conn.recv( size )
        except ( socket.error, struct.error ), e:
            return None
    # read()


    def send( self, msg ):
        try:
            self.conn.send( struct.pack( "!l", len( msg ) ) )
            self.conn.send( msg )
            return True
        except socket.error, e:
            return False
    # send()
# Chat


re_smile = re.compile( "(?P<smile>:-?\))" )
re_sad = re.compile( "(?P<sad>:-?\()" )
re_link = re.compile( "(?P<url>http://\S+)" )

smile = Image( id="smile", filename="smile.png" )
sad = Image( id="sad", filename="sad.png" )


def format( text ):
    text = text.replace( "<", "&lt;" ).replace( ">", "&gt;" )

    text = re_smile.sub( "<img src=\"eagle://smile\" />", text )
    text = re_sad.sub( "<img src=\"eagle://sad\" />", text )
    text = re_link.sub( "<a href=\"\\g<url>\">\\g<url></a>", text )

    return text
# escape


def link_clicked( app, view, url, offset ):
    webbrowser.open_new( url )
# link_clicked()


def send_message( app, button ):
    msg = app[ "entry" ].strip()
    if not msg:
        return

    if not app.chat.conn:
        info( "No connection established!" )
        return

    t = format( msg )

    timestamp = time.strftime( "%Y-%m-%d %H:%M:%S" )
    view = app[ "view" ]
    view.append( """\
<p><font color='#999999'>(%s)</font> <font color="red"><b>you: </b></font>
%s</p>
""" % ( timestamp, t ) )
    app[ "entry" ] = ""
    app.chat.send( msg )
# send_message()


def receive_message( app, file, on_in, on_out, on_urgent, on_error,
                     on_hungup ):

    if on_error or on_hungup:
        app.idle_add( reconnect )
        return False

    msg = app.chat.read()
    if msg is None:
        app.idle_add( reconnect )
        return False

    msg = msg.strip()
    if not msg:
        return True

    t = format( msg )

    timestamp = time.strftime( "%Y-%m-%d %H:%M:%S" )
    view = app[ "view" ]
    view.append( """\
<p><font color='#999999'>(%s)</font> <font color="blue"><b>other: </b></font>
%s</p>
""" % ( timestamp, t ) )

    return True # keep it running
# receive_message()


def create_connection( app ):
    if app.chat:
        app.chat.disconnect()

    if app.last_status_message is not None:
        app.remove_status_message( app.last_status_message )

    host = app[ "host" ]
    port = app[ "port" ]

    app.chat = Chat( host, port, app, receive_message )
    if app.chat.client_mode:
        mid = app.status_message( "Connected to server %s:%d." %
                                  ( host, port ) )
    else:
        mid = app.status_message( "Waiting for clients at port %d." % port )
    app.last_status_message = mid
# create_connection()


def reconnect( app, *ign ):
    create_connection( app )
# reconnect()


app = App( title="Chat",
           statusbar=True,
           preferences=( Entry( id="host",
                                label="Host",
                                value="localhost",
                                ),
                         UIntSpin( id="port",
                                   label="Port",
                                   value=12345,
                                   ),
                         ),
           top=( PreferencesButton(),
                 Button( id="reconnect",
                         label="Reconnect",
                         callback=reconnect,
                         ),
                 ),
           center=( RichText( id="view",
                              label="History:",
                              callback=link_clicked,
                              ),
                    ),
           bottom=( Entry( id="entry",
                           multiline=True,
                           ),
                    Button( id="send",
                            stock="ok",
                            callback=send_message,
                            )
                    )
           )
app.last_status_message = None
app.chat = None
create_connection( app )

run()
