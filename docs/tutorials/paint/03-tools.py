#!/usr/bin/env python2

from eagle import *

class Tool(object):
    """Interface to be implemented by tools."""


    def mouse(self, app, canvas, buttons, x, y):
        """This tool have a user feedback using mouse on canvas."""
        pass



class Line(Tool):
    def __init__(self):
        self.first_point = None


    def mouse(self, app, canvas, buttons, x, y):
        if buttons & Canvas.MOUSE_BUTTON_1:
            if self.first_point is None:
                self.first_point = (x, y)
            else:
                color = app["fg"]
                size  = app["size"]
                x0, y0 = self.first_point
                canvas.draw_line(x0, y0, x, y, color, size)
                self.first_point = None



class Pencil(Tool):
    def __init__(self):
        self.last_point = None


    def mouse(self, app, canvas, buttons, x, y):
        if buttons & Canvas.MOUSE_BUTTON_1:
            color = app["fg"]
            size  = app["size"]
            if self.last_point is not None:
                x0, y0 = self.last_point
            else:
                x0 = x + 1
                y0 = y

            if size == 1:
                canvas.draw_point(x, y, color)
            else:
                half = size / 2
                canvas.draw_rectangle(x-half, y-half, size, size, color, 1,
                                       color, True)
            canvas.draw_line(x0, y0, x, y, color, size)
            self.last_point = (x, y)
        else:
            # Button 1 was released, reset last point
            self.last_point = None



class Rectangle(Tool):
    def __init__(self):
        self.first_point = None


    def mouse(self, app, canvas, buttons, x, y):
        if buttons & Canvas.MOUSE_BUTTON_1:
            if self.first_point is None:
                self.first_point = (x, y)
            else:
                fg   = app["fg"]
                bg   = app["bg"]
                size = app["size"]
                fill = app["rectfill"]

                x0, y0 = self.first_point

                if x0 > x:
                    x0, x = x, x0
                if y0 > y:
                    y0, y = y, y0

                w = x - x0
                h = y - y0

                canvas.draw_rectangle(x0, y0, w, h, fg, size, bg, fill)
                self.first_point = None



class Text(Tool):
    def mouse(self, app, canvas, buttons, x, y):
        if buttons & Canvas.MOUSE_BUTTON_1 and app["text"]:
            text  = app["text"]
            fg    = app["fg"]
            bg    = app["bg"]
            font  = app["font"]

            if app["textbgtransp"]:
                bg = None

            canvas.draw_text(text, x, y, fg, bg, font)



tools = {
    "Line": Line(),
    "Pencil": Pencil(),
    "Rectangle": Rectangle(),
    "Text": Text(),
    }
def_tool="Line"



def canvas_action(app, canvas, buttons, x, y):
    tool = app["tool"]
    tools[tool].mouse(app, canvas, buttons, x, y)



app = App(title="Paint",
           id="paint",
           statusbar=True,
           left=(Color(id="fg",
                         label="Foreground:",
                         color="black",
                         ),
                  Color(id="bg",
                         label="Background:",
                         color=(255, 0, 0),
                         ),
                  Selection(id="tool",
                             label="Tool:",
                             options=tools.keys(),
                             active=def_tool,
                             ),
                  UIntSpin(id="size",
                            label="Line Size:",
                            min=1,
                            value=1,
                            ),
                  ),
           right=(Group(id="textgroup",
                          label="Text Properties:",
                          children=(Entry(id="text",
                                            label="Contents:",
                                            ),
                                     Font(id="font",
                                           label="Font:",
                                           ),
                                     CheckBox(id="textbgtransp",
                                               label="Transparent background?",
                                               ),
                                     ),
                          ),
                   Group(id="rectgroup",
                          label="Rectangle Properties:",
                          children=(CheckBox(id="rectfill",
                                               label="Fill?",
                                               ),
                                     ),
                          ),
                   ),
           top=(SaveFileButton(),
                 CloseButton(),
                 Button(id="undo",
                         stock="undo",
                         ),
                 Button(id="clear",
                         stock="clear",
                         ),
                 ),
           center=(Canvas(id="canvas",
                            label="Draw Here:",
                            width=400,
                            height=400,
                            bgcolor="white",
                            callback=canvas_action,
                            ),
                    )
           )

run()

