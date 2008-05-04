#!/usr/bin/env python2

from eagle import *

def data_changed(app, widget, value):
    print "changed:", app, widget, value
    idx, values = value
    if values:
        values[2] += " [MODIFIED]"
        widget[idx] = values

def selection_changed(app, widget, selected):
    print "seletion:", app, widget, selected


app = App(title="Simple Table",
          left=Table("t1", "List", [1, 2, 3, 4]),
          center=Table("t2", "Table",
                       [[1, True, "Gustavo", 78.0],
                        [3, False, "Test", 80.0],
                        ],
                       headers=["#", "Bool", "Name", "Kg"],
                       editable=True,
                       repositioning=True,
                       expand_columns_indexes=(2,),
                       data_changed_callback=data_changed,
                       selection_callback=selection_changed),
          )

t = app["t1"]
t += 1
print "t:", t
print len(t)
print bool(t)
t[0] = 1234
print t[0]
t[1][0] = 456

print list(t)
print t[-2 : -1]

print t[:]

t = app["t2"]
t[0] = [123, False, "ABC", 12.34]
print "111111111"
t[0][0 : 4] = [False, "BLA", "NADA", 0.1]
print "222222222"

print t
del t[0 : 100]
print t
t[:] = [[0 , True, "A", 0], [1, True, "B", 1], [2, True, "C", 2]]
t[0 : 1] = [[0 , True, "D", 3], [1, True, "E", 4], [2, True, "F", 5]]
t[: 2] = [[0, False, "BLA", 6]]

print t[:]

run()
