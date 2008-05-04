#!/usr/bin/env python

from eagle import *

def callback(app, menuitem):
    info("clicked on menu item %s of %s" % (menuitem, app))

App(title="Test menu",
    menu=(Menu.Item(label="File", callback=callback),
          Menu.Submenu(label="Edit",
                       subitems=(Menu.Item(label="Cut", callback=callback),
                                 Menu.Item(label="Copy", callback=callback),
                                 Menu.Item(label="Paste", callback=callback),
                                 Menu.Separator(),
                                 Menu.Item(label="Inactive", active=False),
                                 Menu.Item(label="Invisible", visible=False),
                                 Menu.Separator(),
                                 Menu.Submenu(label="Sub-Menu",
                                              subitems=(Menu.Item(label="Item1",
                                                                  callback=callback),
                                                        Menu.Item(label="Item2",
                                                                  callback=callback),
                                                        ),
                                              ),
                                 ),
                       ),
          ),
    center=RichText(id="rt",
                    text="""\
<h1>Menu Example</h1>
<p>
  Menus are quite simple in eagle, just give "App" constructor the
  "menu" parameter with a list of Menu.BaseItem subclasses, like
  Menu.Item, Menu.Separator or Menu.Submenu.
</p>
<p>
  In this example, <b>File</b> menu is a single item, while <b>Edit</b>
  have sub-menus and separator example.
</p>
""")
    )

run()
