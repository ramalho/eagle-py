#!/usr/bin/env python2

from eagle import *


App( title="Complex Layout",
     center=Group( id="g0",
                   border=None,
                   horizontal=True,
                   children=( Group( id="g0.0",
                                     border=None,
                                     children=( AboutButton(),
                                                HelpButton() ),
                                     ),
                              Group( id="g0.1",
                                     border=None,
                                     children=( PreferencesButton(),
                                                CloseButton() ),
                                     ),
                              Group( id="g0.2",
                                     border=None,
                                     children=( Entry( id="e0" ),
                                                Entry( id="e1" ) ),
                                     ),
                              Group( id="g0.3",
                                     border=None,
                                     children=Tabs( id="t0",
                                                    children=(
    Tabs.Page( id="p0", label="First", children=Label( label="bla" ) ),
    Tabs.Page( id="p1", label="Second", children=Label( label="ble" ) ),
    ),
                                                    ),
                                     ),
                              ),
                   ),
     )

run()
