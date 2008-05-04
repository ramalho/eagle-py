#!/usr/bin/env python2

from eagle import *

class Tool(object):
    """Interface to be implemented by tools."""


    def mouse(self, app, canvas, buttons, x, y):
        """This tool have a user feedback using mouse on canvas."""
        pass
    # mouse()
# Tool



class Line(Tool):
    def __init__(self):
        self.first_point = None
    # __init__()


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
    # mouse()
# Line



tools = {
    "Line": Line(),
    }
def_tool="Line"



def canvas_action(app, canvas, buttons, x, y):
    tool = app["tool"]
    tools[tool].mouse(app, canvas, buttons, x, y)
# canvas_action()



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

