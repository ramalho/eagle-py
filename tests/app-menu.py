#!/usr/bin/env python

from eagle import *

def callback( app, menuitem ):
    info( "clicked on menu item %s of %s" % ( menuitem, app ) )

App( title="Test menu",
     menu=( App.Menu.Item( "File", callback ),
            App.Menu.Submenu( "Edit",
                              ( App.Menu.Item( "Cut", callback ),
                                App.Menu.Item( "Copy", callback ),
                                App.Menu.Item( "Paste", callback ),
                                App.Menu.Separator(),
                                App.Menu.Item( "Inactive", active=False ),
                                App.Menu.Item( "Invisible", visible=False ),
                                App.Menu.Separator(),
                                App.Menu.Submenu( "Sub-Menu",
                                                  ( App.Menu.Item( "Item1",
                                                                   callback ),
                                                    App.Menu.Item( "Item2",
                                                                   callback ),
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
  "menu" parameter with a list of App.Menu.BaseItem subclasses, like
  App.Menu.Item, App.Menu.Separator or App.Menu.Submenu.
</p>
<p>
  In this example, <b>File</b> menu is a single item, while <b>Edit</b>
  have sub-menus and separator example.
</p>
""" )
     )

run()
