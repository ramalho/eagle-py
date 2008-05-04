#!/usr/bin/env python2

from eagle import *

def selection_changed(app, widget, selected):
    print "seletion:", app, widget, selected
# selection_changed()


class MyType(object):
    def default_value():
        return MyType()
    # default_value()
    default_value = staticmethod(default_value)
# MyType


def cell_format_func(app, table, row, col, value):
    if col == 0:
        return Table.CellFormat(contents=lambda x: "str()=%s" % x)
# cell_format_func()


app = App(title="Simple Table",
          left=(Table(id="t1",
                      label=None,
                      show_headers=False,
                      headers=("Hidden", "Shown"),
                      hidden_columns_indexes=(0,),
                      types=(MyType, str),
                      editable=False,
                      ),
                Table(id="t2",
                      label=None,
                      show_headers=False,
                      headers=("Hidden", "Shown"),
                      hidden_columns_indexes=(0,),
                      types=(MyType, str),
                      editable=True,
                      ),
                Table(id="t3",
                      label=None,
                      show_headers=False,
                      headers=("Hidden", "Shown"),
                      hidden_columns_indexes=(0,),
                      items=((MyType(), "bla"),),
                      editable=True,
                      ),
                Table(id="t4",
                      label=None,
                      show_headers=False,
                      headers=("Hidden", "Shown"),
                      items=((MyType(), "bla"),),
                      editable=True,
                      ),
                Table(id="t5",
                      label=None,
                      show_headers=False,
                      headers=("Hidden", "Shown"),
                      items=((MyType(), "bla"),),
                      cell_format_func=cell_format_func,
                      ),
                )
          )

app["t1"].append((MyType(), "abc"))
app["t1"].append((MyType(), "def"))

app["t2"].append((MyType(), "abc-1"))
app["t2"].append((MyType(), "def-1"))

run()
