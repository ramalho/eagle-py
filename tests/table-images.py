#!/usr/bin/env python2

from eagle import *


App(title="Table with Images",
    center=Table(id="t1",
                 label=None,
                 editable=True,
                 items=((Image(filename="test.png"), "bla"),
                        (Image(filename="test.png"), "123"),
                        ),
                 ),
    )

run()
