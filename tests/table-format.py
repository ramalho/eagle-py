#!/usr/bin/env python2

from eagle import *

def cell_format_func( app, table, row, col, value ):
    if row == 4:
        if col == 1:
            return Table.CellFormat( contents=True )
        elif col == 2:
            return Table.CellFormat( contents=lambda x: x * 5 )
        elif col == 3:
            return Table.CellFormat( contents="This is a fake content" )
    if col == 2:
        if value < 0:
            return Table.CellFormat( bgcolor="red" )
        elif value > 1:
            return Table.CellFormat( strike=True, font="Arial 20" )
        elif value > 0:
            return Table.CellFormat( bgcolor="green" )
        else:
            return Table.CellFormat( bgcolor="yellow" )
    elif col == 3:
        if value == "Good":
            return Table.CellFormat( fgcolor="green", bold=True )
        elif value == "Bad":
            return Table.CellFormat( fgcolor="red", italic=True )
        elif value == "Medium":
            return Table.CellFormat( fgcolor="blue", underline=True )
        elif value == "None":
            return Table.CellFormat( strike=True )
    if col == 1 and row == 1:
        return Table.CellFormat( bgcolor="magenta" )
# cell_format_func()


App( title="Test Table with Cell Format",
     center=Table( id="t1",
                   label="Table",
                   items=( ( "a", True, 1.0, "Good" ),
                           ( "b", False, 2.0, "Bad", ),
                           ( "c", True, -1.0, "Medium" ),
                           ( "d", False, 0.0, "None" ),
                           ( "modified", False, 1.2, "Bla" ) ),
                   cell_format_func=cell_format_func,
                   )
     )
run()
