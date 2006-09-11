#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import time
import re

from threading import Thread, Lock
from decimal import Decimal
from urllib import urlopen
from eagle import *

page_url = "http://www.personnaliteinvestnet.com.br/personnaliteinvestnet/fundos/rentabilidade/mensal/impressaorentabilidade.asp?tipo=per"
re_line = re.compile(
    """\
<tr>\
<td width=145 height=20 valign=top class=tab_textod><img src='[.][.]/img/spacer[.]gif' width=4 height=1><span class=tab_textod>-(?P<desc>.*?)</td>\
<td width=39 height=20 align=right class=tab_textod>(?P<pl_medio>.*?)</td>\
<td width=33 align=right class=tab_textod>(?P<month00>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month01>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month02>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month03>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month04>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month05>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month06>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month07>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month08>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month09>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month10>.*?)&nbsp;</td>\
<td width=33 align=right class=tab_textod>(?P<month11>.*?)&nbsp;</td>\
<td width=48 align=right class=tab_textod>(?P<acc_ano>.*?)&nbsp;</td>\
<td width=48 align=right class=tab_textod>(?P<acc_12>.*?)&nbsp;</td>\
<td width=48 align=right class=tab_textod>(?P<acc_36>.*?)&nbsp;</td>\
<td width=50 align=right class=tab_textod>(?P<adm>.*?)%&nbsp;</td>\
<td width=50 align=right class=tab_textod>(?:.*?)</td>\
</tr>\
""",
    re.M)

current_month = time.localtime()[1] - 1 # 1..12 -> 0..11
month_str = ("Jan",
             "Feb",
             "Mar",
             "Apr",
             "May",
             "Jun",
             "Jul",
             "Aug",
             "Sep",
             "Oct",
             "Nov",
             "Dec")


def populate_table(app):
    """Function to populate tables.

    This function will be put in idle_add(), so it will always run in main,
    graphics thread. We're unable to update GUI from secondary threads!
    """
    hide_with_loss = app["hide_with_loss"]

    pop = []
    for row in app.table:
        if not hide_with_loss:
            pop.append(row)
        else:
            for col in row[1: 15]:
                if col < 0:
                    break
            else:
                pop.append(row)


    graph_items = []
    for row in pop:
        graph_items.append(row[0:4] + [False, row, None])

    calc_items = []
    for row in pop:
        calc_items.append([row[0], Decimal(0)] + row[1:4] + [row])

    app["table"][:] = pop
    app["graph_items"][:] = graph_items
    app["calc_items"][:] = calc_items
    calc_changed(app)
    return False


def add_status_msg(app, msg):
    def f(app):
        try:
            ids = app.statusmsg
        except AttributeError, e:
            app.statusmsg = ids = []

        ids.append(app.status_message(msg))
        return False

    app.idle_add(f)


def clear_status_msg(app):
    def f(app):
        try:
            ids = app.statusmsg
            app.statusmsg = []
        except AttributeError, e:
            return

        for i in ids:
            app.remove_status_message(i)
        return False

    app.idle_add(f)


def download_and_parse_unlocked(app):
    """Download and parse HTML page with data, populate tables.

    This will not do any GUI stuff, it will add populate_table() to be
    called in next idle time from GUI thread using idle_add()
    """

    add_status_msg(app, "downloading url: %s" % page_url)
    contents = urlopen(page_url).read()
    clear_status_msg(app)

    pos_remap = (0, 17, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 1, 2, 3, 16)

    add_status_msg(app, "parsing document...")
    table = []
    results = re_line.finditer(contents)
    for r in results:
        row = [ None ] * len(pos_remap)
        for i, v in enumerate(r.groups()):
            v = v.strip()
            if i == 0:
                v = v.decode('latin1')
            else:
                try:
                    # 1.234,00 -> 1234.00
                    v = v.replace('.', '').replace(',', '.')
                    v = Decimal(v)
                except Exception, e:
                    v = Decimal("0")
            row[pos_remap[i]] = v
        table.append(row)

    def get_whole_col(table, col_idx):
        return [row[col_idx] for row in table]

    app.max_of = {}
    app.min_of = {}
    for i in xrange(1, 18):
        whole_col = get_whole_col(table, i)
        app.max_of[i] = max(*whole_col)
        app.min_of[i] = min(*whole_col)

    clear_status_msg(app)

    app.table = table
    app.idle_add(populate_table)


download_and_parse_lock = Lock()
def download_and_parse(app):
    """Ensure just one processing is done at time"""
    download_and_parse_lock.acquire()
    try:
        try:
            download_and_parse_unlocked(app)
        except Exception, e:
            import traceback
            add_status_msg(app, "Error %s" % e)
            traceback.print_tb(sys.exc_info()[2])
    finally:
        download_and_parse_lock.release()



def cell_format_func(app, table, row, col, value):
    """Highlight main table values"""
    kargs = {}
    if col > 0:
        xalign = Table.CellFormat.XALIGN_RIGHT
        if value == app.min_of[col]:
            kargs["fgcolor"] = "red"
            kargs["bold"] = True
        elif value == app.max_of[col]:
            kargs["fgcolor"] = "blue"
            kargs["bold"] = True
    else:
        xalign = Table.CellFormat.XALIGN_LEFT

    return Table.CellFormat(contents=str, xalign=xalign, **kargs)


def plot(canvas, min_val, max_val, values, color):
    """Plot data values"""
    points = []
    y_scale = (float(max_val) - float(min_val)) / canvas.height
    dx = canvas.width / float(len(values) - 1)

    x = 0
    for v in values:
        y = canvas.height - (float(v) - float(min_val)) / y_scale
        points.append((int(x), int(y)))
        x += dx
    canvas.draw_lines(points, color=color)


def get_colors(n_items):
    """Dumb way to get different colors

    @todo find a smarter color allocation algorithm
    """
    n_var = n_items / 3
    v_color = 255 / (n_var + 1)

    colors = []
    mult = 0
    for i in xrange(n_items):
        c = [255, 255, 255]
        j = i % 3
        if j == 0:
            mult += 1
        c[j] = c[j] - v_color * mult
        colors.append(c)

    return colors


def draw_text_shadow(canvas, text, x, y, color="white"):
    canvas.draw_text(str(text), x + 1, y + 1,
                     font_options=canvas.FONT_OPTION_BOLD,
                     fgcolor="black")
    canvas.draw_text(str(text), x, y,
                     font_options=canvas.FONT_OPTION_BOLD,
                     fgcolor=color)



def draw_graph_info(canvas, min_val, max_val, zero=0):
    """Draw vertical lines, month names and extreme values"""
    color = "#444444"
    month_pos = 20
    x = 0
    dx = float(canvas.width) / 11
    month = current_month - 12
    for i in xrange(12):
        ix = int(x)
        draw_text_shadow(canvas, month_str[month], ix + 2, month_pos, color)
        x += dx
        month += 1
        canvas.draw_line(ix, 0, ix, canvas.height, color)

    draw_text_shadow(canvas, "%0.2f" % max_val, 0, 0)
    draw_text_shadow(canvas, "%0.2f" % min_val, 0, canvas.height - 20)

    if max_val > min_val and min_val < zero < max_val:
        zero_y = canvas.height * (zero - min_val)/(max_val - min_val)
        y = canvas.height - zero_y
        canvas.draw_line(0, y, canvas.width, y, color)


def redraw_graph(app):
    """Check selected values and plot them"""
    selected = [x for x in app["graph_items"] if x[4]]
    canvas = app["graph"]

    # Calculate minimum and maximum values of selected items in order to
    # get the scale
    min_val = 100
    max_val = 0
    for x in selected:
        item = x[5]
        for m in item[4:16]:
            min_val = min(m, min_val)
            max_val = max(m, max_val)

    canvas.clear()

    if not selected:
        return

    draw_graph_info(canvas, min_val, max_val)

    colors = get_colors(len(selected))
    for color, x in zip(colors, selected):
        item = x[5]
        values = item[4:16]
        values.reverse()
        x[6] = color # remember graph color, to use in cell_format_func_graph()
        plot(canvas, min_val, max_val, values, color)

def redraw_graph2(app):
    """Check selected values and plot them"""
    selected = [x for x in app["graph_items"] if x[4]]
    canvas = app["graph2"]

    capital = []

    # Calculate minimum and maximum values of selected items in order to
    # get the scale
    min_val = 1000
    max_val = 1000
    for x in selected:
	capital.append([])
	PV = 1000
	# capital[-1].append(PV)
        item = x[5]
	ble = item[4:16]
	ble.reverse()
        for m in ble:
	    PV *= 1+(m/100)
	    capital[-1].append(PV)
            min_val = min(PV, min_val)
            max_val = max(PV, max_val)

    canvas.clear()

    if not selected:
        return

    draw_graph_info(canvas, min_val, max_val, 1000)

    i = 0
    colors = get_colors(len(selected))
    for color, x in zip(colors, selected):
        values = capital[i]
        x[6] = color # remember graph color, to use in cell_format_func_graph()
        plot(canvas, min_val, max_val, values, color)
	i = i + 1


def graph_selected(app, table, rows):
    """Toggle item selection"""
    if not rows:
        return

    idx, row = rows[0]
    v = not row[4]
    table[idx][4] = v
    if not v:
        table[idx][6] = None
    redraw_graph(app)
    redraw_graph2(app)


def cell_format_func_graph(app, table, row, col, value):
    """If item is selected, change the background to match graph color"""
    r = table[row]
    kargs = {}
    if r[4] and r[6]:
        kargs["bgcolor"] = r[6]
    if 1 <= col <= 3:
        kargs["xalign"] = Table.CellFormat.XALIGN_RIGHT

    return Table.CellFormat(**kargs)


def reload(app, button):
    """Launch a thread to do the download and parse"""
    t = Thread(target=download_and_parse, args=(app,))
    t.start()


def toggle_with_loss(app, checkbox, value):
    populate_table(app)


def cell_format_func_calc(app, table, row, col, value):
    kargs = {}
    if col == 1:
        kargs["contents"] = "%0.2f" % value
        if abs(value - app.min_calc) < 10:
            kargs["bold"] = True
            kargs["fgcolor"] = "red"
        elif abs(value - app.max_calc) < 10:
            kargs["bold"] = True
            kargs["fgcolor"] = "blue"
    return Table.CellFormat(**kargs)


def calc_changed(app, *args):
    app.min_calc = sys.maxint
    app.max_calc = 0

    n_months = app["n_months"]

    for row in app["calc_items"]:
        plan = row[5]
        amount = Decimal(app["amount"])
        for i in plan[4 : 4 + n_months]:
            v = 1 + i / Decimal("100.00")
            amount *= v

        row[1] = amount
        app.min_calc = min(amount, app.min_calc)
        app.max_calc = max(amount, app.max_calc)



page_data = Tabs.Page(label="Data",
                      children=(Table(id="table",
                                      label=None,
                                      show_headers=True,
                                      headers=("Description",
                                               "Yield Year",
                                               "Yield 12",
                                               "Yield 36",
                                               month_str[current_month - 1],
                                               month_str[current_month - 2],
                                               month_str[current_month - 3],
                                               month_str[current_month - 4],
                                               month_str[current_month - 5],
                                               month_str[current_month - 6],
                                               month_str[current_month - 7],
                                               month_str[current_month - 8],
                                               month_str[current_month - 9],
                                               month_str[current_month - 10],
                                               month_str[current_month - 11],
                                               month_str[current_month - 12],
                                               "Tax (%)",
                                               "Equity (R$ MM 12month)"),
                                      types=(str,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal),
                                      cell_format_func=cell_format_func),
                                ),
                      )

page_graph = Tabs.Page(label="Graph",
                       children=(Table(id="graph_items",
                                       label=None,
                                       show_headers=True,
                                       expand_columns_indexes=0,
                                       hidden_columns_indexes=(5, 6),
                                       cell_format_func=cell_format_func_graph,
                                       selection_callback=graph_selected,
                                       headers=("Name",
                                                "Yield Year",
                                                "Yield 12",
                                                "Yield 36",
                                                "Graph it?",
                                                "Object",
                                                "Color"),
                                       types=(str,
                                              Decimal,
                                              Decimal,
                                              Decimal,
                                              bool,
                                              object,
                                              object)),
				Group(id="graficos", label="", children=(
                                 Canvas(id="graph",
                                        label=None,
                                        width=500,
                                        height=350,
                                        scrollbars=False,
                                        expand_policy=ExpandPolicy.Nothing()),
                                 Canvas(id="graph2",
                                        label=None,
                                        width=500,
                                        height=350,
                                        scrollbars=False,
                                        expand_policy=ExpandPolicy.Nothing()),), horizontal=True),
                                 ),
                       )

page_calc = Tabs.Page(label="Calculator",
                      children=(Table(id="calc_items",
                                      label=None,
                                      show_headers=True,
                                      expand_columns_indexes=0,
                                      hidden_columns_indexes=5,
                                      cell_format_func=cell_format_func_calc,
                                      headers=("Name",
                                               "Result",
                                               "Yield Year",
                                               "Yield 12",
                                               "Yield 36",
                                               "Object"),
                                      types=(str,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             Decimal,
                                             object)),
                                UIntSpin(id="n_months",
                                         label="Months:",
                                         value=12,
                                         max=12,
                                         callback=calc_changed),
                                UIntSpin(id="amount",
                                         label="Initial Amount:",
                                         value=5000,
                                         step=1000,
                                         callback=calc_changed),
                                ),
                      )



app = App(title="Itaú Personnalité",
          statusbar=True,
          center=(Tabs(id="tabs",
                       children=(page_data,
                                 page_graph,
                                 page_calc,
                                 ),
                       ),
                  CheckBox(id="hide_with_loss",
                           label="No loss acceptable",
                           callback=toggle_with_loss),
                  ),
          bottom=Button(id="reload", stock="refresh", callback=reload)
          )
app.max_calc = None
app.min_calc = None

app.timeout_add(1000, reload, app["reload"])
run()
