#!/usr/bin/env python2

from eagle import *

def add_option(app, button):
    selection = app.get_widget_by_id("selection")
    v = app["entry"]
    if not v:
        info("You must type something in 'entry' box")
        return

    try:
        selection.append(v, True)
    except ValueError:
        info("Option '%s' already added!" % v)
# add_option()


def remove_option(app, button):
    selection = app.get_widget_by_id("selection")
    v = app["entry"]
    if not v:
        info("You must type something in 'entry' box")
        return

    try:
        selection -= v
        ## same as:
        # selection.remove(v)
    except ValueError:
        info("'%s' was not an option!" % v)
# remove_option()


App(title="Selection box capabilities",
    left=(Selection(id="selection",
                    options=("opt1", "opt2"),
                    value="opt1",
                    ),
          Entry(id="entry"),
          ),
    right=(Button(id="add",
                  stock="add",
                  callback=add_option,
                  ),
           Button(id="remove",
                  stock="remove",
                  callback=remove_option,
                  ),
           ),
    )

run()
