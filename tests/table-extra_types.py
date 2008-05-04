#!/usr/bin/env python2

from eagle import *

def f(app, table, row_idx):
    info("clicked: %s, %s, row_idx=%d" % (app, table, row_idx))


app = App(title="Table with datetime",
          center=(Table("t1", "Table with Progress",
                        types=(str, Table.ProgressCell),
                        items=[["ten percent", 10],
                               ["fifty percent", 50],
                               ["ninety percent", 90],
                               ],
                        headers=["Text", "Progress"],
                        expand_columns_indexes=(0,),
                        ),
                  Table("t2", "Table with Buttons",
                        types=(str, Table.ButtonCell),
                        items=[["test 1", f],
                               ["test 2", f],
                               ["test 3", f],
                               ],
                        headers=["Text", "Action"],
                        expand_columns_indexes=(0,),
                        ),
                  )
          )

run()
