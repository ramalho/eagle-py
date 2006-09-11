#!/usr/bin/python2

from eagle import *


App(title="Table without scrollbars",
    top=(Table(id="t-without-scrollbars",
               label=None,
               items=("table without scrollbars",),
               scrollbars=False,
               expand_policy=ExpandPolicy.FillVertical(),
               ),
         Table(id="t-witho-scrollbars",
               label=None,
               items=("table with scrollbars",),
               scrollbars=True,
               ),
         )
    )

run()
