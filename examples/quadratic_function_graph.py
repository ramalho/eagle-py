#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from eagle import *
import math

epsilon = 0.000001
graph_font_size = 8


def clear(app, button):
    app["graph"].clear()


def quadratic(a, b, c, x):
    return a * (x ** 2) + b * x + c


def data_changed(app, *args):
    a = app["a"]
    b = app["b"]
    c = app["c"]
    graph = app["graph"]

    if abs(a) < epsilon:
        error("You must provide a Second Degree Polynom.")
        return

    delta = (b ** 2) - (4 * a * c)
    if delta < 0:
        print("Complex root not supported: delta (%s) < 0" % delta)
        return

    graph.clear()
    delta_sqrt = math.sqrt(delta)

    r0 = (-b - delta_sqrt) / (2 * a)
    r1 = (-b + delta_sqrt) / (2 * a)

    # f(x) = ax² + bx + c
    # f'(x) = 2ax + b
    # center_x: f'(center_x) == 0: 2a*center_x + b == 0; center_x = -b/2a
    # center_y: f(center_x) == a*center_x² + b*center_x + c
    #           a*(-b/2a)² + b*(-b/2a) + c
    #           b²/4a - b²/2a + c
    #           (b² - 2b² + 4ac)/4a
    #           (-b² + 4ac)/4a
    #           -(b² - 4ac)/4a   = -delta/4a
    center_x = -b / (2 * a)
    center_y = -delta / (4 * a)
    extreme_y = quadratic(a, b, c, r0)

    # draw some area around roots
    d = abs(r1 - r0) / 4.0
    if d < epsilon:
        # both roots have the same value
        d = float(graph.width) / float(graph.height)

    if r0 > r1:
        r0, r1 = r1, r0

    x0 = r0 - d
    x1 = r1 + d

    if a > 0:
        y0 = center_y - d
        y1 = extreme_y + d
    else:
        y0 = extreme_y - d
        y1 = center_y + d

    scale_x = (x1 - x0) / float(graph.width)
    scale_y = (y1 - y0) / float(graph.height)

    i2 = int((center_x - x0) / scale_x)
    j = int((extreme_y - y0) / scale_y)
    # If visible, draw y-axis
    if x0 <= 0 <= x1:
        i = int(-x0 / scale_x)
        graph.draw_line(i, 0, i, graph.height, color="#666666", size=1)
    else:
        if x0 > 0:
            i = graph.width
        else:
            i = 0

    graph.draw_line(i, j, i2, j, color="#999999")
    txt = str(center_y)
    j += 2
    graph.draw_text(txt, i, j, fgcolor="red", font_size=graph_font_size)


    # If visible, draw x-axis (should always be)
    if y0 <= 0 <= y1:
        j = graph.height - int(-y0 / scale_y)
        graph.draw_line(0, j, graph.width, j, color="#666666", size=1)
        j += 2

        i = int((r0 - x0) / scale_x)
        graph.draw_line(i, j - 12, i, j + 10, color="#999999")
        txt = str(r0)
        graph.draw_text(txt, i, j, fgcolor="red", font_size=graph_font_size)

        i = int((r1 - x0) / scale_x)
        graph.draw_line(i, j - 12, i, j + 10, color="#999999")
        txt = str(r1)
        graph.draw_text(txt, i, j, fgcolor="red", font_size=graph_font_size)


    # Sample points, we'll draw as connected lines
    points = []
    x = x0
    for i in xrange(graph.width):
        y = quadratic(a, b, c, x)
        j = graph.height - int((y - y0) / scale_y)
        points.append((i, j))
        x += scale_x

    graph.draw_lines(points, color="red")


    # Draw text with expression and roots
    if a < 0:
        y = 0
    else:
        y = graph.height - 30

    txt = ("f(x) = %0.3e * x² + %0.3e * x + %0.3e\n"
           "roots: { %s, %s }") % (a, b, c, r0, r1)
    graph.draw_text(txt, 2, y, fgcolor="red", bgcolor="white",
                    font_size=graph_font_size)




App(title="Second Degree Polynom Graph and Roots",
    data_changed_callback=data_changed,
    window_size=(800, 600),
    top=(Spin(id="a", label="x² * ", value=1.0, digits=5),
         Spin(id="b", label="+ x * ", value=-1.0),
         Spin(id="c", label="+ ", value=-2),
         ),
    center=Canvas(id="graph",
                  width=700,
                  height=400,
                  label=None,
                  bgcolor="white",
                  scrollbars=False),
    bottom=(Button(id="calc", label="Calculate", callback=data_changed),
            Button(id="clear", stock="clear", callback=clear),
            ),
    )

run()
