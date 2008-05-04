#!/usr/bin/env python2

from eagle import *

filename = None
changes = False
sb_lastid = []

def populate_table(table, fname):
    # clear table
    del table[:]

    # populate from file
    # Line format is:
    # [export] varname=["]contents["]
    f = open(fname, "r")
    for ln, line in enumerate(f):
        try:
            var, contents = line.split("=")
            var = var.strip()
            var = var.split(" ")
            if var[0] == "export":
                export = True
                var = var[1]
            else:
                export = False
                var = var[0]

            contents = contents.strip()
            if contents.startswith('\'') or contents.startswith('"'):
                contents = contents[1 :]
            if contents.endswith('\'') or contents.endswith('"'):
                contents = contents[: -1]

            table.append((export, var, contents))
        except:
            error("Error processing line %d: %r" % (ln, line))

    f.close()


def save_table(table, fname):
    f = open(fname, "w")
    for n, (export, var, contents) in enumerate(table):
        if not (var and contents):
            error("Invalid line %d skipped" % n)
            continue

        if export:
            f.write("export ")
        f.write("%s=%r\n" % (var, contents))
    f.close()


def set_no_changes(app):
    for id in sb_lastid:
        app.remove_status_message(id)

    del sb_lastid[:]

    global changes
    changes = False
    set_inactive("save", app)

def set_filename(app, fname=None):
    global filename

    if fname:
        app["filename"] = "File: %s" % fname
        filename = fname
    else:
        app["filename"] = "No file selected!"
        filename = None


def choose_file(app, button, fname):
    if changes:
        msg = "There is still unsaved data! Continue and discard them?"
        if not yesno(msg):
            return

    set_filename(app, fname)
    if fname:
        populate_table(app["vars"], fname)
        set_no_changes(app)


def data_changed(app, table, data):
    global changes
    changes = True
    sb_lastid.append(app.status_message("Changes still not saved!"))
    set_active("save", True, app)


def save_file(app, button):
    fname = filename
    while fname is None:
        fname = app.file_chooser(FileChooser.ACTION_SAVE)

    set_filename(app, fname)

    save_table(app["vars"], filename)

    set_no_changes(app)


def quit(app):
    if changes:
        return yesno("There is still unsaved data. Exit and discard data?")
    else:
        return True


app = App(title="Variables Editor",
          help="""\
Edit shell variables from text file.
""",
          quit_callback=quit,
          statusbar=True,
          top=(OpenFileButton(callback=choose_file),
               Button(id="save",
                      stock="save",
                      callback=save_file),
               ),
          center=(Label(id="filename"),
                  Table(id="vars",
                        label="Variables",
                        headers=("Export", "Variable", "Value"),
                        types=(bool, str, str),
                        editable=True,
                        expand_columns_indexes=(2,),
                        data_changed_callback=data_changed,
                        ),
                  ),
          )

set_filename(app, None)
set_inactive("save", app)

run()
