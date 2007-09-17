#!/usr/bin/env python2

from eagle import *

# Must be alive when using, so put in img_test until the end of application
img_test = Image( id="test", filename="test.png" )

def img_provider( filename ):
    if filename.startswith( "myapp://" ):
        data = chr( 127 ) * 22 * 22 * 3
        return Image( data=data, width=22, height=22 )
# img_provider()


def clear( app, button ):
    app[ "richtext" ].set_text( "" )
# clear()

def append( app, button ):
    app[ "richtext" ].append( "<p>another paragraph!</p>" )
# append()




App( title="Rich Text Example",
     center=( RichText( id="richtext",
                        img_provider=img_provider,
                        text="""\
<h1>level 1 header</h1>
<h2>level 2 header</h2>
<h3>level 3 header</h3>
<p>Here is a paragraph, followed by horizontal rule</p>
<hr />

<div align="left">Left-aligned text</div>

<div align="center">Centered text</div>

<div align="right">Right-aligned text</div>

<div align="justified">Justified text filling the whole horizontal space.
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc Abc
</div>

<hr />

<p>List of styles:</p>
<ul>
   <li><b>bold</b></li>
   <li><i>italic</i></li>
   <li><font family="serif">serif font</font></li>
   <li><font color="red" bgcolor="blue">red fore, blue background</font></li>
   <ol>
      <li><img src="test.png" /></li>
      <li><img src="test.png" width="16" /></li>
      <li><img src="test.png" height="16" /></li>
      <li><img src="test.png" width="16" height="32"/></li>
      <li><img src="eagle://test" /></li>
      <li><img src="myapp://" /></li>
   </ol>
   <ol>
      <li>other numbered list item</li>
      <li>other numbered list item</li>
   </ol>
</ul>
<a href="http://www.gustavobarbieri.com.br">external url</a><br />
<a href=\"#end-anchor\">go to end of this page</a>
<font bgcolor=\"#d9d9d9\">
<pre>
# we also support pre formatted text:
def function( arg0, arg1, *args, **kargs ):
    print "arg0:", arg0
    print "arg1:", arg1
    print "args:", args
    print "kargs:", kargs
</pre>
</font>
<br />
<br />
<a name="end-anchor">end of page</a>
"""
                        ),
              ),
     bottom=(
              Button( id="clear", stock="clear", callback=clear ),
              Button( id="append", stock="add", callback=append ),
              )
     )

run()
