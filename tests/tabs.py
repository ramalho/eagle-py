#!/usr/bin/env python2

from eagle import *


def bt0( app, widget ):
    print "app", app
    print "t0:", app["t0"]
    try:
        app[ "t0" ][ "Change-me" ] = "Changed"
    except KeyError, e:
        info( "Exception: %s" % e )

    print "t0, page 2 label is", app[ "t0" ].get_page( 2 )
# bt0()


def disable_4( app, widget ):
    app[ "t0" ].get_page( 4 ).set_inactive()
# disable_4()


def enable_4( app, widget ):
    app[ "t0" ].get_page( 4 ).set_active()
# enable_4()


def hide_3( app, widget ):
    app[ "t0" ].get_page( 3 ).hide()
# hide_3()


def show_3( app, widget ):
    app[ "t0" ].get_page( 3 ).show()
# show_3()


def focus_0( app, widget ):
    app[ "t0" ].focus_page( 0 )
# focus_0()


def focus_4( app, widget ):
    app[ "t0" ][ 4 ].focus()
# focus_4()


App( title="Test Tabs",
     center=( Tabs( id="t0",
                    children=( Tabs.Page( label="First",
                                          children=Label( label="bla" ),
                                          ),
                               Tabs.Page( label="Second",
                                          children=( CloseButton(),
                                                     AboutButton(),
                                                     Button( id="disable_4",
                                                             label="Disable 4",
                                                             callback=disable_4,
                                                             ),
                                                     Button( id="enable_4",
                                                             label="Enable 4",
                                                             callback=enable_4,
                                                             ),
                                                     Button( id="hide_3",
                                                             label="Hide 3",
                                                             callback=hide_3,
                                                             ),
                                                     Button( id="show_3",
                                                             label="Show 3",
                                                             callback=show_3,
                                                             ),
                                                     Button( id="focus_0",
                                                             label="Focus 0",
                                                             callback=focus_0,
                                                             ),
                                                     Button( id="focus_4",
                                                             label="Focus 4",
                                                             callback=focus_4,
                                                             ),
                                                     ),
                                          horizontal=True,
                                          ),
                               Tabs.Page( label="Change-me",
                                          children=( Button( id="bt0",
                                                             label="do it!",
                                                             callback=bt0,
                                                             ),
                                                     ),
                                          ),
                               Tabs.Page( label="Hide",
                                          children=Entry( id="a" ),
                                          ),
                               Tabs.Page( label="Disable",
                                          children=Entry( id="b" ),
                                          ),
                               ),
                    ),
              ),
     )

run()
