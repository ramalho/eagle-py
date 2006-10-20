#!/usr/bin/env python

from eagle import *

def callback():
    print "menu clicked"

App( title="Test menu",
     menu=( ( "File", callback),
            ( "Edit", ( ( "Cut", callback),
                        ( "----", None ),
                        ( "Copy", callback),
                        ( "Paste", callback),
                        "---",
                        ( "Sub-Menu", ( ( "Sub-sub-item1", callback ),
                                        ( "Sub-sub-item2", callback ),
                                        ),
                          ),
                        ),
              ),
            ),
     center=RichText( id="rt",
                      text="""\
<h1>Menu Example</h1>
<p>
  Menus are quite simple in eagle, just give "App" constructor the
  "menu" parameter with a list of pairs (label, action), where action
  can be a callable object with the menu action or another list of pairs,
  to create submenus.
</p>
<p>
  In this example, <b>File</b> menu is a single item, while <b>Edit</b>
  have sub-menus and separator example.
</p>
""" )
     )

run()
