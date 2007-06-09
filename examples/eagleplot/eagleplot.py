#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Time-stamp: <2007-06-08 16:48:45 nilton>
# Function Plotter for Eagle
# Nilton Volpato 2007

from eagle import *
from adaptive_sampling import ASPlotter, Stats, AUTO, ALL
import math

graph_font_size = 8

exported_syms = (('sin', math.sin),
                 ('cos', math.cos),
                 ('pi', math.pi),
                 ('exp', math.exp))

class ASEaglePlotter(ASPlotter):
    def __init__(self,
                 plot_range=ALL,
                 aspect_ratio=0.618034,
                 **kwargs):
        ASPlotter.__init__(self, **kwargs)
        self.plot_range = plot_range
        self.aspect_ratio = aspect_ratio

    def plot_graph(self, app, f, tmin, tmax):
        graph = app["graph"]
        graph.clear()
        W, H = graph.width, graph.height

        self.adaptive_sampling(f, tmin, tmax)

        st = Stats(self.points)
        if self.plot_range == AUTO:
            xmax, xmin, ymax, ymin = st.bbox_auto(self.points)
        else:
            xmax, xmin, ymax, ymin = st.bbox()
        wd, ht = xmax - xmin, ymax - ymin

        if wd == 0 or ht == 0:
            # graph width or height is 0, probably user is
            # typing and auto_plot is on, so no info()
            return

        border_size = 5

        W = int(H / self.aspect_ratio)

        _sx = (W - 2 * border_size) / wd
        def sx(x):
            return int(_sx * (x - xmin)) + border_size
        _sy = (self.aspect_ratio * W - 2 * border_size) / ht
        def sy(y):
            return H - int(_sy * (y - ymin)) - border_size

        #sx = W/wd
        #sy = self.aspect_ratio*W/ht

        #print 'W:', W, 'H:', H
        #print 'WD:', wd, 'HT:', ht, sx, sy

        if app['axis']:
            # Y axis
            if xmin <= 0 <= xmax:
                x_yaxis = 0
            else:
                x_yaxis = (xmax + xmin)/2
            graph.draw_line(sx(x_yaxis), 0,
                            sx(x_yaxis), H,
                            color='black', size=1)

            # XXX Need a better algorithm to draw ticks
            interval = 10 * int(math.log10(ht))
            if interval == 0:
                interval = 1
            tick = int(interval * int(ymin / interval))
            while tick < ymax:
                graph.draw_line(sx(x_yaxis) - 3, sy(tick),
                                sx(x_yaxis),   sy(tick),
                                color='black', size=1)
                graph.draw_text(' ' + str(tick),
                                sx(x_yaxis), sy(tick) - graph_font_size / 2,
                                fgcolor='black', font_size=graph_font_size)
                tick += interval

            # X axis
            if ymin <= 0 <= ymax:
                y_xaxis = 0
            else:
                y_xaxis = (ymax + ymin) / 2
            graph.draw_line(0, sy(y_xaxis),
                            W, sy(y_xaxis),
                            color='black', size=1)

            # XXX Need a better algorithm to draw ticks
            interval = 10 * int(math.log10(wd))
            if interval == 0:
                interval = 1
            tick = int(interval * int(xmin / interval))
            while tick < xmax:
                if tick == 0:
                    tick += interval
                graph.draw_line(sx(tick), sy(y_xaxis),
                                sx(tick), sy(y_xaxis) - 3,
                                color='black', size=1)
                graph.draw_text(str(tick),
                                sx(tick) - graph_font_size / 3,
                                sy(y_xaxis) + graph_font_size / 2,
                                fgcolor='black', font_size=graph_font_size)
                tick += interval


        pts = [(sx(p.x), sy(p.y)) for p in self.points]

        graph.draw_lines(pts, color="red")
        #for p in pts:
        #    graph.draw_rectangle(p[0]-1, p[1]-1, 2, 2,
        #                         filled=True, color="black")


class GraphParamException(ValueError):
    def __init__(self, widget, message):
        ValueError.__init__(self, message)
        self.widget = widget


def get_func(app, wid_id):
    wid = app.get_widget_by_id(wid_id)
    func_spec = wid.get_value()
    if not func_spec:
        msg = "Please specify function %s" % wid.label
        raise GraphParamException(wid, msg)
    try:
        globaldict = {'__builtins__': dict(exported_syms)}
        exec "def func(t):\n   return %s" % func_spec in globaldict
        func = globaldict["func"]
        del globaldict["func"]
        return func
    except Exception, e:
        msg = 'Invalid function %s "%s": %s' % (wid.label, func_spec, e)
        raise GraphParamException(wid, msg)


def get_interval_for_func(app, wid_id, func):
    wid = app.get_widget_by_id(wid_id)
    spec = wid.get_value()
    try:
        globaldict = {'__builtins__': dict(exported_syms)}
        value = eval(spec, globaldict)
        func(value) # check if function itself evaluates fine
        return value
    except Exception, e:
        msg = 'Invalid value for interval %s "%s": %s' % (wid.label, spec, e)
        raise GraphParamException(wid, msg)


def get_graph_params(app):
    func_x = get_func(app, "x(t)")
    func_y = get_func(app, "y(t)")
    f = lambda t: (func_x(t), func_y(t))
    tmin = get_interval_for_func(app, "tmin", f)
    tmax = get_interval_for_func(app, "tmax", f)
    return (f, tmin, tmax)


def check_graph_params(app):
    try:
        f, tmin, tmax = get_graph_params(app)
        return True
    except GraphParamException, e:
        return False


def plot_graph_internal(app):
    plotter = ASEaglePlotter(
        plot_range={'All': ALL, 'Automatic': AUTO}[app['plotrange']],
        aspect_ratio={'1:1': 1.0, '1:GoldenRatio':0.618034}[app['aspect']],
        )
    f, tmin, tmax = get_graph_params(app)
    plotter.plot_graph(app, f, tmin, tmax)
    return plotter


def plot_graph(app, *args):
    try:
        plot_graph_internal(app)
    except GraphParamException, e:
        info(str(e))
        e.widget.focus()


def clear_graph(app, button):
    app["graph"].clear()


def set_sample(app, *args):
    sample = samples[app['demo']]
    for k, v in sample.iteritems():
        app[k] = v
    if not app["auto_plot"]: # otherwise it was already plotted
        plot_graph(app)


def resize_canvas_cb(app, canvas, width, height):
    canvas.resize(width, height)
    if app["auto_plot"]:
        try:
            plot_graph_internal(app)
        except GraphParamException, e:
            pass


def data_changed_cb(app, widget, value):
    if widget.id != "auto_plot":
        try:
            plot_graph_internal(app)
        except GraphParamException, e:
            pass


def save_graph_cb(app, widget, filename):
    try:
        plotter = plot_graph_internal(app)
        plotter.write_to_file(filename)
    except GraphParamException, e:
        info(str(e))
        e.widget.focus()


samples = {
    "f(x) = (t-1)*(t-3)*(t-4)": {'x(t)': 't',
                                 'y(t)': '(t - 1) * (t-3) * (t-4)',
                                 'tmin': '0.5', 'tmax': '4.5',
                                 'plotrange': 'All',
                                 'aspect': '1:GoldenRatio'},

    "(5*cos(5*t), 5*sin(3*t))": {'x(t)': '5 * cos(5 * t)',
                                 'y(t)': '5 * sin(3 * t)',
                                 'tmin': '0', 'tmax': '2 * pi',
                                 'plotrange': 'All',
                                 'aspect': '1:1'},

    "(5*sin(t), 5*cos(t))":     {'x(t)': '5 * sin(t)',
                                 'y(t)': '5 * cos(t)',
                                 'tmin': '0', 'tmax': '2 * pi',
                                 'plotrange': 'All',
                                 'aspect': '1:1'},

    "f(x) = 1/x":               {'x(t)': 't',
                                 'y(t)': '1 / t',
                                 'tmin': '-1.0', 'tmax': '1.0',
                                 'plotrange': 'Automatic',
                                 'aspect': '1:GoldenRatio'},

    "(5*t, 5*sin(1/t))":        {'x(t)': '5 * t',
                                 'y(t)': '5 * sin(1 / t)',
                                 'tmin': '-2.0', 'tmax': '2.0',
                                 'plotrange': 'Automatic',
                                 'aspect': '1:GoldenRatio'},

    "f(x) = 3**(-x**2)":        {'x(t)': 't',
                                 'y(t)': '3 ** (-t ** 2)',
                                 'tmin': '-5', 'tmax': '5',
                                 'plotrange': 'Automatic',
                                 'aspect': '1:GoldenRatio'},

    "flower":                   {'x(t)': '(1 + sin(5.0 * t) / 5.0) * cos(t)',
                                 'y(t)': '(1 + sin(5.0 * t) / 5.0) * sin(t)',
                                 'tmin': '0', 'tmax': '2 * pi',
                                 'plotrange': 'All',
                                 'aspect': '1:1'},

    "t**5+sin(2*pi*t),t+exp(t)":{'x(t)': 't ** 5 + sin(2 * pi * t)',
                                 'y(t)': 't + exp(t)',
                                 'tmin': '-1.3', 'tmax': '1.3',
                                 'plotrange': 'Automatic',
                                 'aspect': '1:GoldenRatio'},

    "epicycloid":               {'x(t)': '31 * cos(t) - 7 * cos(31 * t / 7)',
                                 'y(t)': '31 * sin(t) - 7 * sin(31 * t / 7)',
                                 'tmin': '0', 'tmax': '12 * pi',
                                 'plotrange': 'Automatic',
                                 'aspect': '1:1'},
    }


App(
    title="Parametric Function Plotting",
    author="Nilton Volpato",
    window_size=(800, 700),
    data_changed_callback=data_changed_cb,
    top=(Group(id="g1", label="Parametric Function",
               children=[Entry(id="x(t)", label="x(t)"),
                         Entry(id="y(t)", label="y(t)")]),
         Group(id="g2", label='Interval "t"',
               children=[Entry(id="tmin", label="min"),
                         Entry(id="tmax", label="max")],
               expand_policy=ExpandPolicy.FillVertical()),
         Group(id="g3", label="Options",
               children=[Selection(id="plotrange", label="Plot Range",
                                   options=["All","Automatic"],
                                   value="Automatic"),
                         Selection(id="aspect", label="Aspect Ratio",
                                   options=["1:1", "1:GoldenRatio"],
                                   value="1:GoldenRatio"),
                         CheckBox(id="axis", label="Draw Axis", value=True)],
               expand_policy=ExpandPolicy.FillVertical()),
         Group(id="g4", label="Samples",
               children=[Selection(id="demo", callback=set_sample,
                                   label=None, options=samples.keys())],
               expand_policy=ExpandPolicy.FillVertical()),
         ),
    center=Canvas(id="graph", label=None,
                  width=1, height=1, #width=700, height=433,
                  bgcolor="white", resize_callback=resize_canvas_cb),
    bottom=(Button(id="plot", label="Plot Graph", callback=plot_graph),
            Button(id="clear", stock="clear", callback=clear_graph),
            SaveFileButton(id="save", filter="*.pdf", callback=save_graph_cb),
            CheckBox(id="auto_plot", label="Automatic plot on changes.",
                     value=True, persistent=True))
    )

run()
