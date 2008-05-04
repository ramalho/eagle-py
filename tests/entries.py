#!/usr/bin/env python2

from eagle import *

def changed(app, entry, value):
    print "app %s, entry %s, value %r" % (app.id, entry.id, value)


App(title="Entries Test",
    center=(Entry(id="single"),
            Entry(id="multi", multiline=True),
            Entry(id="non-editable",
                  label="non-editable", value="Value", editable=False),
            Entry(id="non-editable-multi",
                  label="non-editable", value="Value", editable=False,
                  multiline=True),
            ),
    data_changed_callback=changed,
    )

run()
