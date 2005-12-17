#!/usr/bin/env python2

from eagle import *

def print_data( app, button ):
    print "rot_hor:", get_value( "rot_hor", app )
    print "color:", app[ "color" ]
    print "pizza:", app[ "pizza" ]

    print "active?", get_value( "active", app )
    print "something:", get_value( "name", app )
# print_data()


def change_color( app, button ):
    app[ "color" ] = "green"
# change_color()


def hide_group( app, button ):
    if hide_group.hidden:
        show( "group", app )
    else:
        hide( "group", app )

    hide_group.hidden = not hide_group.hidden
# hide_group()
hide_group.hidden = False


def toggle_spin_active( app, button ):
    if toggle_spin_active.active:
        set_inactive( "rot_hor", app )
    else:
        set_active( "rot_hor", True, app )

    toggle_spin_active.active = not toggle_spin_active.active
# toggle_spin_active()
toggle_spin_active.active = True


def raise_exception( app, button ):
    raise Exception( "As requested, this exception was raised." )
# raise_exception()

def changed( app, widget, value ):
    print app.id, widget.id, "changed to", value
# changed()


def mouse_callback( app, widget, button, x, y ):
    color = app[ "color" ]
    canvas = app[ "canvas" ]
    if mouse_callback.last_point is not None:
        x0, y0 = mouse_callback.last_point
        canvas.draw_line( x0, y0, x, y, color=color )
    mouse_callback.last_point = x, y
# mouse_callback()
mouse_callback.last_point = None


def file_choose( app, widget, filename ):
    print app.id, widget.id, filename
# file_choose()


App( title="test app",
     author="Gustavo Sverzut Barbieri <barbieri@gmail.com>",
     version="0.1",
     license="GNU LGPL",
     description="""\
Test application to demonstrate library features.
""",
     help="""\
I have nothing to help you.
""",
     preferences=(
    Entry( id="username",
           label="Username:" ),
    Password( id="password",
              label="Password:" ),
    ),
     left=(
    UIntSpin( id="rot_hor",
              label="Horizontal:",
              value=45,
              max=360,
              step=10,
              callback=changed,
              persistent=True,
              ),
    HSeparator(),
    Group( id="group",
           label="Group:",
           children=(
                    CheckBox( id="active",
                              label="Active?",
                              state=True,
                              callback=changed
                              ),
                    Entry( id="name",
                           label="Name:",
                           value="Something",
                           callback=changed
                           ),
                    )
           ),
    Color( id="color",
           label="My Color:",
           color=0xffff00,
           callback=changed,
           persistent=True,
           ),
    Button( id="print_data", label="Print Data", callback=print_data ),
    Button( id="change_color", label="Change color", callback=change_color ),
    Button( id="hide_group", label="Hide Group", callback=hide_group ),
    Button( id="toggle_spin_active", label="Toggle Spin Active",
            callback=toggle_spin_active ),
    Button( id="raise_exception", label="Raise Exception",
            callback=raise_exception ),
    ),
     right=(
    Selection( id="pizza",
               label="Pizza:",
               options=( "Cheese",
                         "Peperoni",
                         "Marguerita",
                         ),
               active="Peperoni",
               callback=changed,
               ),
    HelpButton(),
    AboutButton(),
    CloseButton(),
    Label( label="A simple text label" ),
    Progress( id="progress",
              label="Progress:",
              value=0.5,
              ),
    HSeparator(),
    OpenFileButton( filter="image/png", callback=file_choose ),
    SelectFolderButton( callback=file_choose),
    SaveFileButton( callback=file_choose ),
    HSeparator(),
    Font( "font", label="My Font:" ),
    Canvas( id="dummy2",
            label="dummy", width=800, height=600 )
    ),
     center=(
    Canvas( id="canvas",
            label="Draw here",
            bgcolor="white",
            width=800, height=600,
            callback=mouse_callback,
            ),
    Canvas( id="dummy",
            label="dummy", width=800, height=600 )
    ),
     top=(
    PreferencesButton(),
    ),
     bottom=(
    CloseButton(),
    QuitButton(),
    ),
     data_changed_callback=changed,
     )

App( title="bla", left=CloseButton() )

run()
