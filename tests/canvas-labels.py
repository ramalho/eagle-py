#!/usr/bin/env python2

from eagle import *

def change_nonexistent(app, button):
    if not yesno("This will raise an exception and close the application.\n"
                 "Continue?"):
        return
    v = app.get_widget_by_id(button.id[1 :])
    v.set_label("Make it crash")
# change_nonexistent()

def change_placeholder(app, button):
    v = app.get_widget_by_id(button.id[1 :])
    v.set_label("New Label")
# change_placeholder()


App(title="Canvas test using label and scrollbars properties",
    left=(Canvas(id="c0",
                 width=400,
                 height=400,
                 label="With label"),
          Canvas(id="c1",
                 width=400,
                 height=400,
                 label=None),
          Canvas(id="c2",
                 width=400,
                 height=400,
                 label=""),
          Button(id="bc1",
                 label="crash changing non-existent label",
                 callback=change_nonexistent),
          Button(id="bc2",
                 label="change placeholder",
                 callback=change_placeholder),
          ),
    right=(Canvas(id="c0.1",
                  width=400,
                  height=400,
                  label="With label",
                  scrollbars=False),
           Canvas(id="c1.1",
                  width=400,
                  height=400,
                  label=None,
                  scrollbars=False),
           Canvas(id="c2.1",
                  width=400,
                  height=400,
                  label="",
                  scrollbars=False),
           Button(id="bc1.1",
                  label="crash changing non-existent label",
                  callback=change_nonexistent),
           Button(id="bc2.1",
                  label="change placeholder",
                  callback=change_placeholder),
           )
    )

run()
