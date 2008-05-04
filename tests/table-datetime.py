#!/usr/bin/env python2

from eagle import *
import datetime

def data_changed(app, widget, value):
    print "changed:", app, widget, value
# data_changed()

def selection_changed(app, widget, selected):
    print "seletion:", app, widget, selected
# selection_changed()


app = App(title="Table with datetime",
          center=(Table("t1", "Table with Date",
                        [["Gustavo", datetime.date(1982, 6, 19)],
                         ["Today", datetime.date.today()]
                         ],
                        headers=["Name", "Date"],
                        editable=True,
                        repositioning=True,
                        expand_columns_indexes=(1,),
                        data_changed_callback=data_changed,
                        selection_callback=selection_changed),
                  Table("t2", "Table with Date and Time",
                        [["Now", datetime.datetime.now()]
                         ],
                        headers=["Name", "Date/Time"],
                        editable=True,
                        repositioning=True,
                        expand_columns_indexes=(1,),
                        data_changed_callback=data_changed,
                        selection_callback=selection_changed),
                  )
          )

run()
