#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2005 by Gustavo Sverzut Barbieri
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Changed: $LastChangedBy$ at $LastChangedDate$

__author__ = "Gustavo Sverzut Barbieri"
__author_email__ = "barbieri@gmail.com"
__license__ = "LGPL"
__url__ = "http://code.gustavobarbieri.com.br/eagle/"
__version__ = "0.1"
__revision__ = "$Rev$"
__description__ = """\
Eagle is an abstraction layer atop Graphical Toolkits focused on
making simple applications easy to build while powerful in features.
"""
__long_description__ = """\
Eagle is an abstraction layer atop Graphical Toolkits focused on
making simple applications easy to build while powerful in features.

With Eagle you have many facilities to build application that needs
just some buttons, user input and a canvas to draw.

Canvas is really simple, what makes Eagle a great solution to
Computer Graphics and Image Processing software, the primary focus
of this library.

User input widgets are persistent, you just need to mark them
"persistent" or put them in the preferences area.

Eagle is not meant to be another Graphical Toolkit, you already
have a bunch of them, like Qt, Gtk, wxWidgets (to name just a few).
It's focused on applications that have few windows, with buttons,
simple user input and canvas. Widgets are laid out automatically
in 5 areas: left, right, top, bottom and center.

It provides useful widgets like: Color selector, Font selector,
Quit button, Preferences button and bialog, About dialog and Help
dialog.
"""
__doc__ = __long_description__

__all__ = [
    "run", "quit", "get_value", "set_value",
    "get_app_by_id", "get_widget_by_id",
    "show", "hide", "set_active", "set_inactive", "close",
    "App",
    "Entry", "Password",
    "Spin", "IntSpin", "UIntSpin",
    "CheckBox",
    "Progress",
    "Color", "Font",
    "Button", "AboutButton", "CloseButton", "QuitButton", "HelpButton",
    "OpenFileButton", "SelectFolderButton", "SaveFileButton",
    "PreferencesButton",
    "Selection",
    "Group",
    "HSeparator", "VSeparator",
    "Label",
    "Canvas", "Image",
    "information", "info", "error", "err", "warning", "warn",
    "yesno", "confirm",
    ]

import os
import sys
import gc
import pygtk
pygtk.require( "2.0" )
import gtk
import pango
import gobject
import cPickle as pickle

required_gtk = ( 2, 6, 0 )
m = gtk.check_version( *required_gtk )
if m:
    raise SystemExit(
        ( "Error checking GTK version: %s. "
          "This system requires pygtk >= %s, you have %s installed." )
        % ( m,
            ".".join( [ str( v ) for v in required_gtk ] ),
            ".".join( [ str( v ) for v in gtk.pygtk_version ] )
            ) )


_apps = {}


def _gen_ro_property( name, doc="" ):
    """Generates a Read-Only property.

    The generated property can be assigned only one value, if this value
    is not None, it cannot be changed.
    """
    naming = "__ro_%s__" % ( name, )
    def get( self ):
        try:
            return getattr( self, naming )
        except AttributeError:
            return None
    # get()
    def set( self, value ):
        try:
            v = getattr( self, naming )
        except AttributeError:
            v = None
        if v is None:
            setattr( self, naming, value )
        else:
            raise Exception( "Read Only property '%s'." % ( name, ) )
    # set()
    return property( get, set, None, doc )
# _gen_ro_property()


def _callback_tuple( callback ):
    if not isinstance( callback, ( tuple, list ) ):
        if callback is None:
            return tuple()
        elif callable( callback ):
            return ( callback, )
        else:
            raise TypeError( "Callback '%s' is not callable!" % ( callback, ) )
    else:
        for c in callback:
            if not callable( c ):
                raise TypeError( "Callback '%s' is not callable!" % ( c, ) )
        return callback
# _callback_tuple()


def _str_tuple( string ):
    if not isinstance( string, ( tuple, list ) ):
        if string is None:
            return tuple()
        else:
            return ( str( string ), )
    else:
        return tuple( [ str( s ) for s in string ] )
# _str_tuple()


def _obj_tuple( obj ):
    if not isinstance( obj, ( tuple, list ) ):
        if obj is None:
            return tuple()
        else:
            return ( obj, )
    else:
        return tuple( obj )
# _obj_tuple()


def _set_icon_list( gtkwidget, stock_id ):
    style = gtkwidget.get_style()
    iconset = style.lookup_icon_set( stock_id )
    if iconset:
        icons = []
        for s in iconset.get_sizes():
            i = iconset.render_icon( style,
                                     gtk.TEXT_DIR_NONE,
                                     gtk.STATE_NORMAL,
                                     s,
                                     gtkwidget,
                                     None
                                     )
            icons.append( i )
        gtkwidget.set_icon_list( *icons )
# _set_icon_list()


class _Table( gtk.Table ):
    """Internal widget to arrange components in tabular form.

    @warning: never use it directly in Eagle applications!
    """

    padding = 3
    id = _gen_ro_property( "id" )
    children = _gen_ro_property( "children" )
    horizontal = _gen_ro_property( "horizontal" )


    def __init__( self, id, children, horizontal=False ):
        self.id = id
        self.horizontal = horizontal
        self.children = _obj_tuple( children )

        gtk.Table.__init__( self )

        self.set_name( id )
        self.set_homogeneous( False )
        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        """Lay out components in a horizontal or vertical table."""
        if not self.children:
            return

        n = len( self.children )

        if self.horizontal:
            self.resize( 2, n )
        else:
            self.resize( n, 2 )

        for idx, c in enumerate( self.children ):
            w = c.__get_widgets__()
            xrm, yrm = c.__get_resize_mode__()
            if len( w ) == 1:
                if self.horizontal:
                    row0 = 0
                    row1 = 2
                    col0 = idx
                    col1 = idx + 1
                else:
                    row0 = idx
                    row1 = idx + 1
                    col0 = 0
                    col1 = 2

                self.attach( w[ 0 ], col0, col1, row0, row1,
                             xoptions=xrm,
                             yoptions=yrm,
                             xpadding=self.padding,
                             ypadding=self.padding )
            elif len( w ) == 2:
                if self.horizontal:
                    row0 = 0
                    row1 = 1
                    row2 = 1
                    row3 = 2
                    col0 = idx
                    col1 = idx + 1
                    col2 = idx
                    col3 = idx + 1
                else:
                    row0 = idx
                    row1 = idx + 1
                    row2 = idx
                    row3 = idx + 1
                    col0 = 0
                    col1 = 1
                    col2 = 1
                    col3 = 2
                self.attach( w[ 0 ], col0, col1, row0, row1,
                             xoptions=xrm,
                             yoptions=yrm,
                             xpadding=self.padding,
                             ypadding=self.padding )
                self.attach( w[ 1 ], col2, col3, row2, row3,
                             xoptions=xrm,
                             yoptions=yrm,
                             xpadding=self.padding,
                             ypadding=self.padding )
    # __setup_gui__()


    def __get_widgets__( self ):
        return self.children
    # __get_widgets__()
# _Table


class _Panel( gtk.ScrolledWindow ):
    """Internal widget to arrange components.

    @warning: never use it directly in Eagle applications!
    """

    spacing = 5
    app = _gen_ro_property( "app" )
    id = _gen_ro_property( "id" )
    children = _gen_ro_property( "children" )

    _horizontal = None
    _hscrollbar_policy = None
    _vscrollbar_policy = None

    def __init__( self, app, id, children ):
        self.app = app
        self.id = id
        self.children = _obj_tuple( children )

        gtk.ScrolledWindow.__init__( self )
        self.set_name( id )
        self.__setup_gui__()
        self.__add_widgets_to_app__()
    # __init__()


    def __setup_gui__( self ):
        self.set_shadow_type( gtk.SHADOW_NONE )
        self.set_policy( hscrollbar_policy=self._hscrollbar_policy,
                         vscrollbar_policy=self._vscrollbar_policy )
        self._tab = _Table( self.id, self.children, self._horizontal )
        self.add_with_viewport( self._tab )
        self.get_child().set_shadow_type( gtk.SHADOW_NONE )
    # __setup_gui__()


    def __add_widgets_to_app__( self ):
        for w in self.children:
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()


    def __get_widgets__( self ):
        return self._tab.__get_widgets__()
    # __get_widgets__()
# _Panel


class _VPanel( _Panel ):
    """Internal widget to arrange components vertically.

    @warning: never use it directly in Eagle applications!
    """

    _horizontal = False
    _hscrollbar_policy = gtk.POLICY_NEVER
    _vscrollbar_policy = gtk.POLICY_AUTOMATIC
# _VPanel


class _HPanel( _Panel ):
    """Internal widget to arrange components horizontally.

    @warning: never use it directly in Eagle applications!
    """

    _horizontal = True
    _hscrollbar_policy = gtk.POLICY_AUTOMATIC
    _vscrollbar_policy = gtk.POLICY_NEVER
# _HPanel


class _EGObject( object ):
    """The basic Eagle Object.

    All eagle objects provides an attribute "id".

    @warning: never use it directly in Eagle applications!
    """

    id = _gen_ro_property( "id" )

    def __init__( self, id ):
        self.id = id
    # __init__()


    def __str__( self ):
        return "%s( id=%r )" % ( self.__class__.__name__, self.id )
    # __str__()
    __repr__ = __str__
# _EGObject


class AutoGenId( object ):
    """Mix-In to auto-generate ids.

    @warning: never use it directly in Eagle applications!
    """
    last_id_num = 0

    def __get_id__( classobj ):
        n = "%s-%d" % ( classobj.__name__, classobj.last_id_num )
        classobj.last_id_num += 1
        return n
    # __get_id__()
    __get_id__ = classmethod( __get_id__ )
# AutoGenId


class Image( _EGObject, AutoGenId ):
    """
    An image that can be loaded from files or binary data and saved to files.
    """

    def __init__( self, **kargs ):
        """Image constructor.

        Images can be constructed in 2 ways using keyword arguments:
         - from files, in this case you give it B{filename} keyword:

              >>> Image( filename='myfile.png' )

         - from raw data, in this case you need to provide at least
           B{data}, B{width} and B{height} as arguments. Optional
           arguments are I{depth}, I{has_alpha} and I{row_stride}.
           See L{load_data()} for more information:

              >>> Image( data=data, width=200, height=200, depth=32, has_alpha=False )

        @see: L{load_data()}
        @see: L{load_file()}
        """
        _EGObject.__init__( self, self.__get_id__() )

        self._img = None

        if "filename" in kargs:
            self.load_file( kargs[ "filename" ] )
        elif "data" in kargs and "width" in kargs and "height" in kargs:
            k = { "data": kargs[ "data" ],
                  "width": kargs[ "width" ],
                  "height": kargs[ "height" ],
                }
            if "depth" in kargs:
                k[ "depth" ] = kargs[ "depth" ]
            if "has_alpha" in kargs:
                k[ "has_alpha" ] = kargs[ "has_alpha" ]
            if "rowstride" in kargs:
                k[ "rowstride" ] = kargs[ "rowstride" ]
            self.load_data( **k )
        elif "__int_image__" in kargs:
            if isinstance( kargs[ "__int_image__" ], gtk.gdk.Pixbuf ):
                self._img = kargs[ "__int_image__" ]
            else:
                raise ValueError( "Wrong internal image given!" )
        elif len( kargs ) > 0:
            params = [ "%s=%r" % kv for kv in kargs.iteritems() ]
            raise ValueError( "Unknow parameters: %s" % params )
    # __init__()


    def __get_gtk_pixbuf__( self ):
        return self._img
    # __get_gtk_pixbuf__()


    def __del__( self ):
        gc.collect()
    # __del__()


    def save( self, filename, format=None, **options ):
        """Save image to a file.

        If format is not specified, it will be guessed from filename.

        Format may be an extension or a mime type, see
        L{get_writable_formats()}.

        @see: L{get_writable_formats()}.
        @raise Exception: if errors happened during write
        @raise ValueError: if format is unsupported
        """
        if isinstance( filename, ( tuple, list ) ):
            filename = os.path.join( *filename )

        if format is None:
            format = filename.split( os.path.extsep )[ -1 ]

        format = format.lower()
        t = None
        for f in self.get_writable_formats():
            if format == f[ "name" ] or \
               format in f[ "extensions" ] or \
               format in f[ "mime_types" ]:
                t = f[ "name" ]
                break
        if t:
            try:
                self._img.save( filename, t, options )
            except gobject.GError, e:
                raise Exception( e )
        else:
            raise ValueError( "Unsupported file format: \"%s\"" % format )
    # save()


    def get_formats( self ):
        """Get supported image format information.

        @return: list of dicts with keys:
         - B{name}: format name
         - B{description}: format description
         - B{extensions}: extensions that match format
         - B{mime_types}: mime types that match format
         - B{is_writable}: if it is possible to write in this format, otherwise
           it's just readable
        """
        return gtk.gdk.pixbuf_get_formats()
    # get_formats()


    def get_writable_formats( self ):
        """Get formats that support saving/writing.

        @see: L{get_formats()}
        """
        k = []
        for f in self.get_formats():
            if f[ "is_writable" ]:
                k.append( f )
        return k
    # get_writable_formats()


    def load_file( self, filename ):
        """Load image from file given its filename.

        filename may be a string or a tuple/list with path elements,
        this helps your program to stay portable across different platforms.

           >>> i = Image()
           >>> i.load_file( 'img.png' )
           >>> i.load_file( ( 'test', 'img.png' ) )
        """
        if isinstance( filename, ( tuple, list ) ):
            filename = os.path.join( *filename )

        try:
            self._img = gtk.gdk.pixbuf_new_from_file( filename )
        except gobject.GError, e:
            raise Exception( e )
    # load_file()


    def load_data( self, data, width, height,
                   depth=24, has_alpha=None, rowstride=None ):
        """Load image from raw data.

        If no value is provided as B{has_alpha}, then it's set to C{False}
        if B{depth} is less or equal 24 or set to C{True} if depth is 32.

        If no value is provided as B{rowstride}, then it's set to
        M{width * depth / bits_per_sample}.

           >>> i = Image()
           >>> i.load_data( my_data1, 800, 600, depth=32, has_alpha=False )
           >>> i.load_data( my_data2, 400, 300, depth=24 )
        """
        colorspace = gtk.gdk.COLORSPACE_RGB
        bits_per_sample = 8

        if has_alpha is None:
            if depth <= 24:
                has_alpha=False
            else:
                has_alpha=True

        if rowstride is None:
            rowstride = width * depth / bits_per_sample

        if len( data ) < height * rowstride:
            raise ValueError( ( "data must be at least "
                                "width * height * rowstride long."
                                "Values are: data size=%d, required=%d" ) %
                              ( len( data ), height * rowstride ) )

        if isinstance( data, list ):
            # Convert to allowed types, from fastest to slower
            try:
                import Numeric
                data = Numeric.array( data, typecode=Numeric.Character )
            except ImportError:
                try:
                    import array
                    data = array.array( 'c', data )
                except:
                    data = tuple( data )

        self._img = gtk.gdk.pixbuf_new_from_data( data, colorspace,
                                                  has_alpha, bits_per_sample,
                                                  width, height, rowstride )
    # load_data()


    def get_data( self ):
        """Return raw data and information about this image.

        @return: a tuple of:
         - width
         - height
         - depth
         - has alpha?
         - rowstride
         - raw pixel data
        """
        return ( self.get_width(), self.get_height(), self.get_depth(),
                 self.has_alpha(), self.get_rowstride(),
                 self._img.get_pixels() )
    # get_data()

    def get_width( self ):
        return self._img.get_width()
    # get_width()


    def get_height( self ):
        return self._img.get_height()
    # get_height()


    def get_size( self ):
        """Return a tuple ( width, heigt )"""
        return ( self.get_width(), self.get_height() )
    # get_size()


    def get_rowstride( self ):
        """Row stride is the allocated size of a row.

        Generally, rowstride is the number of elements in a row multiplied
        by the size of each element (bits per pixel).

        But there are cases that there is more space left, a padding, to
        align it to some boundary, so you may get different value for
        row stride.
        """
        return self._img.get_rowstride()
    # get_rowstride()


    def get_n_channels( self ):
        """Number of channels."""
        return self._img.get_n_channels()
    # get_n_channels()


    def get_bits_per_pixel( self ):
        """Bits per pixel"""
        return self.get_n_channels() * self._img.get_bits_per_sample()
    # get_bits_per_pixel()
    get_depth = get_bits_per_pixel


    def has_alpha( self ):
        """If it has an alpha channel"""
        return self._img.get_has_alpha()
    # has_alpha()
# Image



class _EGWidget( _EGObject ):
    """The base of every Graphical Component in Eagle.

    @warning: never use it directly in Eagle applications!
    """
    app = _gen_ro_property( "app" )

    def __init__( self, id, app=None ):
        _EGObject.__init__( self, id )
        if app is not None:
            self.app = app
        self._widgets = tuple()
    # __init__()


    def __get_resize_mode__( self ):
        "Return a tuple with ( horizontal, vertical ) resize mode"
        return ( gtk.FILL, gtk.FILL )
    # __get_resize_mode__()


    def __get_widgets__( self ):
        """Return a list of B{internal} widgets this Eagle widget contains.

        @warning: never use it directly in Eagle applications!
        """
        return self._widgets
    # __get_widgets__()


    def set_active( self, active=True ):
        """Set the widget as active.

        An active widget have their actions enabled, while an inactive
        (active=False) will be grayed and actions disabled.
        """
        for w in self.__get_widgets__():
            w.set_sensitive( active )
    # set_active()


    def set_inactive( self ):
        """Same as L{set_active}( False )"""
        self.set_active( False )
    # set_inactive()


    def show( self ):
        """Make widget visible."""
        for w in self.__get_widgets__():
            w.show()
    # show()


    def hide( self ):
        """Make widget invisible."""
        for w in self.__get_widgets__():
            w.hide()
    # hide()
# _EGWidget


class _EGDataWidget( _EGWidget ):
    """The base of every Eagle widget that holds data.

    Widgets that holds data implement the interface with L{get_value}() and
    L{set_value}().

    It can be made persistent with L{persistent}=True
    """
    persistent = False

    def __init__( self, id, persistent, app=None ):
        _EGObject.__init__( self, id )
        if app is not None:
            self.app = app
        self.persistent = persistent
        self._widgets = tuple()
    # __init__()


    def get_value( self ):
        """Get data from this widget."""
        raise NotImplementedError
    # get_value()

    def set_value( self, value ):
        """Set data to this widget."""
        raise NotImplementedError
    # set_value()
# _EGDataWidget


class AboutDialog( _EGWidget, AutoGenId ):
    """A window that displays information about the application.

    @attention: avoid using this directly, use L{AboutButton} instead.
    """
    border = 12
    spacing = 6
    width = 600
    height = 400
    margin = 6

    def __init__( self, app,
                  title, author=None, description=None, help=None,
                  version=None, license=None, copyright=None ):
        _EGWidget.__init__( self, self.__get_id__(), app )
        self.title = str( title )
        self.author = _str_tuple( author )
        self.description = _str_tuple( description )
        self.help = _str_tuple( help )
        self.version = _str_tuple( version )
        self.license = _str_tuple( license )
        self.copyright = _str_tuple( copyright )

        self.__setup_gui__()
    # __init__()


    def __del__( self ):
        self._diag.destroy()
    # __del__()


    def __setup_gui__( self ):
        win = self.app.__get_window__()
        btns = ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE )
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        self._diag = gtk.Dialog( title=( "About: %s" % self.title ),
                                 parent=win,
                                 flags=flags, buttons=btns )

        self._diag.set_border_width( self.border )
        self._diag.set_default_size( self.width, self.height )
        self._diag.set_has_separator( False )
        self._diag.vbox.set_spacing( self.spacing )

        _set_icon_list( self._diag, gtk.STOCK_ABOUT )

        self._sw = gtk.ScrolledWindow()
        self._diag.vbox.pack_start( self._sw, expand=True, fill=True )

        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )
        self._sw.set_shadow_type( gtk.SHADOW_IN )

        self._text = gtk.TextView()
        self._sw.add( self._text )
        self._text.set_editable( False )
        self._text.set_cursor_visible( False )
        self._text.set_wrap_mode( gtk.WRAP_WORD )
        self._text.set_left_margin( self.margin )
        self._text.set_right_margin( self.margin )

        self.__setup_text__()
    # __setup_gui__()


    def __setup_text__( self ):
        buf = self._text.get_buffer()
        big = buf.create_tag( "big", scale=pango.SCALE_XX_LARGE )
        bold = buf.create_tag( "bold", weight=pango.WEIGHT_BOLD )
        italic = buf.create_tag( "italic", style=pango.STYLE_ITALIC )
        i = buf.get_start_iter()
        ins = buf.insert_with_tags

        ins( i, self.title, big, bold )

        if self.version:
            ins( i, "\n" )
            ins( i, ".".join( self.version ), italic )

        ins( i, "\n\n" )

        if self.description:
            for l in self.description:
                ins( i, l )
                ins( i, "\n" )
            ins( i, "\n\n" )

        if self.license:
            ins( i, "License: ", bold )
            ins( i, ", ".join( self.license ) )
            ins( i, "\n" )

        if self.author:
            if len( self.author ) == 1:
                ins( i, "Author:\n", bold )
            else:
                ins( i, "Authors:\n", bold )
            for a in self.author:
                ins( i, "\t" )
                ins( i, a )
                ins( i, "\n" )
            ins( i, "\n\n" )

        if self.help:
            ins( i, "Help:\n", bold )
            for l in self.help:
                ins( i, l )
                ins( i, "\n" )
            ins( i, "\n\n" )

        if self.copyright:
            ins( i, "Copyright:\n", bold )
            for l in self.copyright:
                ins( i, l )
                ins( i, "\n" )
            ins( i, "\n\n" )
    # __setup_text__()


    def run( self ):
        self._diag.show_all()
        self._diag.run()
        self._diag.hide()
    # run()
# AboutDialog


class HelpDialog( _EGWidget, AutoGenId ):
    """A window that displays application help.

    @attention: avoid using this directly, use L{HelpButton} instead.
    """
    border = 12
    spacing = 6
    width = 600
    height = 400
    margin = 6

    def __init__( self, app, title, help=None ):
        _EGWidget.__init__( self, self.__get_id__(), app )
        self.title = title
        self.help = _str_tuple( help )
        self.__setup_gui__()
    # __init__()


    def __del__( self ):
        self._diag.destroy()
    # __del__()


    def __setup_gui__( self ):
        win = self.app.__get_window__()
        btns = ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE )
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        self._diag = gtk.Dialog( title=( "Help: %s" % self.title ),
                                 parent=win,
                                 flags=flags, buttons=btns )
        self._diag.set_border_width( self.border )
        self._diag.set_default_size( self.width, self.height )
        self._diag.set_has_separator( False )
        self._diag.vbox.set_spacing( self.spacing )
        _set_icon_list( self._diag, gtk.STOCK_HELP )

        self._sw = gtk.ScrolledWindow()
        self._diag.get_child().pack_start( self._sw, expand=True, fill=True )

        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )
        self._sw.set_shadow_type( gtk.SHADOW_IN )

        self._text = gtk.TextView()
        self._sw.add( self._text )
        self._text.set_editable( False )
        self._text.set_cursor_visible( False )
        self._text.set_wrap_mode( gtk.WRAP_WORD )
        self._text.set_left_margin( self.margin )
        self._text.set_right_margin( self.margin )

        self.__setup_text__()
    # __setup_gui__()


    def __setup_text__( self ):
        buf = self._text.get_buffer()
        big = buf.create_tag( "big", scale=pango.SCALE_XX_LARGE )
        bold = buf.create_tag( "bold", weight=pango.WEIGHT_BOLD )
        italic = buf.create_tag( "italic", style=pango.STYLE_ITALIC )
        i = buf.get_start_iter()
        ins = buf.insert_with_tags

        ins( i, self.title, big, bold )
        ins( i, "\n\n" )

        ins( i, "Help:\n", bold )
        for l in self.help:
            ins( i, l )
            ins( i, "\n" )
    # __setup_text__()


    def run( self ):
        self._diag.show_all()
        self._diag.run()
        self._diag.hide()
    # run()
# HelpDialog


class FileChooser( _EGWidget, AutoGenId ):
    """A dialog to choose a file.

    @attention: avoid using this directly, use L{App.file_chooser},
    L{OpenFileButton}, L{SaveFileButton} or L{SelectFolderButton} instead.
    """
    ACTION_OPEN = 0
    ACTION_SAVE = 1
    ACTION_SELECT_FOLDER = 2
    ACTION_CREATE_FOLDER = 3

    def __init__( self, app, action, filename=None,
                  title=None, filter=None, multiple=False ):
        """Dialog to choose files.

        filter may be a single pattern (ie: '*.png'), mime type
        (ie: 'text/html') or a list of patterns or mime types or
        a list of lists, each sub list with a filter name and mime type/
        patterns accepted. Examples:
          [ [ 'Images', '*.ppm', 'image/jpeg', 'image/png' ],
            [ 'Text', '*.text', 'text/plain' ],
          ]
        """
        _EGWidget.__init__( self, self.__get_id__(), app )
        self.action = action
        self.filter = filter
        self.multiple = multiple or False
        self.filename = filename
        self.title = title  or self.__gen_title__()

        self.__setup_gui__()
    # __init__()


    def __gen_title__( self ):
        t = { self.ACTION_OPEN: "Open: %s",
              self.ACTION_SAVE: "Save: %s",
              self.ACTION_SELECT_FOLDER: "Open Folder: %s",
              self.ACTION_CREATE_FOLDER: "Create Folder: %s",
              }
        title = t.get( self.action, t[ self.ACTION_OPEN ] )
        return title % self.app.title
    # __gen_title__()


    def __del__( self ):
        self._diag.destroy()
    # __del__()


    def __setup_gui__( self ):
        win = self.app.__get_window__()
        a = { self.ACTION_OPEN: gtk.FILE_CHOOSER_ACTION_OPEN,
              self.ACTION_SAVE: gtk.FILE_CHOOSER_ACTION_SAVE,
              self.ACTION_SELECT_FOLDER: gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
              self.ACTION_CREATE_FOLDER: gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
              }.get( self.action, gtk.FILE_CHOOSER_ACTION_OPEN )

        b = ( gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT,
              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
        self._diag = gtk.FileChooserDialog( title=self.title,
                                            parent=win,
                                            action=a,
                                            buttons=b )
        _set_icon_list( self._diag, gtk.STOCK_OPEN )
        self._diag.set_select_multiple( self.multiple )
        if self.filter:
            if isinstance( self.filter, ( tuple, list ) ):
                for f in self.filter:
                    filter = gtk.FileFilter()
                    if isinstance( f, ( tuple, list ) ):
                        filter.set_name( f[ 0 ] )
                        for e in f[ 1 : ]:
                            if '/' in e:
                                filter.add_mime_type( e )
                            else:
                                filter.add_pattern( e )
                    elif isinstance( f, ( str, unicode ) ):
                        filter.set_name( f )
                        if '/' in f:
                            filter.add_mime_type( f )
                        else:
                            filter.add_pattern( f )
                    else:
                        raise ValueError( "invalid filter!" )
                    self._diag.add_filter( filter )

            elif isinstance( self.filter, ( str, unicode ) ):
                filter = gtk.FileFilter()
                filter.set_name( self.filter )
                if '/' in self.filter:
                    filter.add_mime_type( self.filter )
                else:
                    filter.add_pattern( self.filter )
                self._diag.set_filter( filter )
            else:
                raise ValueError( "invalid filter!" )
        if self.filename:
            self._diag.set_filename( self.filename )
    # __setup_gui__()


    def run( self ):
        self._diag.show_all()
        r = self._diag.run()
        self._diag.hide()
        if r == gtk.RESPONSE_ACCEPT:
            return self._diag.get_filename()
        else:
            return None
    # run()
# FileChooser


class PreferencesDialog( _EGWidget, AutoGenId ):
    """A dialog to present user with preferences.

    Preferences is another L{App} area, just like C{left}, C{right}, C{center},
    C{top} or C{bottom}, but will be displayed in a separate window.

    @attention: avoid using this directly, use L{PreferencesButton} instead.
    """
    def __init__( self, app, children ):
        _EGWidget.__init__( self, self.__get_id__(), app )
        self.children = _obj_tuple( children )
        self.__setup_gui__()
        self.__add_widgets_to_app__()
    # __init__()


    def __del__( self ):
        self._diag.destroy()
    # __del__()


    def __setup_gui__( self ):
        win = self.app.__get_window__()
        btns = ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE )
        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
        self._diag = gtk.Dialog( title=( "Preferences: %s" % self.app.title ),
                                 parent=win,
                                 flags=flags, buttons=btns )
        self._diag.set_default_size( 400, 300 )
        _set_icon_list( self._diag, gtk.STOCK_PREFERENCES )

        self._sw = gtk.ScrolledWindow()
        self._diag.get_child().pack_start( self._sw, expand=True, fill=True )

        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )

        self._tab = _Table( self.id, self.children )
        self._sw.add_with_viewport( self._tab )
        self._sw.get_child().set_shadow_type( gtk.SHADOW_NONE )
        self._sw.set_shadow_type( gtk.SHADOW_NONE )
    # __setup_gui__()


    def __add_widgets_to_app__( self ):
        for w in self.children:
            if isinstance( w, _EGDataWidget ):
                w.persistent = True
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()


    def run( self ):
        self._diag.show_all()
        self._diag.run()
        self._diag.hide()
    # run()
# PreferencesDialog


class DebugDialog( _EGObject, AutoGenId ):
    """Dialog to show uncaught exceptions.

    This dialog shows information about uncaught exceptions and also save
    the traceback to a file.
    """
    # Most of DebugDialog code came from Gazpacho code! Thanks!
    border = 12
    spacing = 6
    width = 600
    height = 400
    margin = 6

    def __init__( self ):
        _EGObject.__init__( self, self.__get_id__() )
        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        b = ( gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE )
        self._diag = gtk.Dialog( "Application Crashed!",
                                 parent=None,
                                 flags=gtk.DIALOG_MODAL,
                                 buttons=b )
        self._diag.set_border_width( self.border )
        self._diag.set_default_size( self.width, self.height )
        self._diag.set_has_separator( False )
        self._diag.vbox.set_spacing( self.spacing )

        self._hbox1 = gtk.HBox()

        self._label1 = gtk.Label( "<b>Exception type:</b>" )
        self._label1.set_use_markup( True )
        self._hbox1.pack_start( self._label1, False, False, self.spacing )
        self._label1.show()

        self._exctype = gtk.Label()
        self._hbox1.pack_start( self._exctype, False, True )
        self._exctype.show()

        self._diag.vbox.pack_start( self._hbox1, False, False )
        self._hbox1.show()

        self._hbox2 = gtk.HBox()

        self._label2 = gtk.Label( "<b>This info was saved to:</b>" )
        self._label2.set_use_markup( True )
        self._hbox2.pack_start( self._label2, False, False, self.spacing )
        self._label2.show()

        self._save_name = gtk.Label()
        self._hbox2.pack_start( self._save_name, False, True )
        self._save_name.show()

        self._diag.vbox.pack_start( self._hbox2, False, False )
        self._hbox2.show()

        self._sw = gtk.ScrolledWindow()
        self._sw.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC )
        self._sw.set_shadow_type( gtk.SHADOW_IN )
        self._text = gtk.TextView()
        self._text.set_editable( False )
        self._text.set_cursor_visible( False )
        self._text.set_wrap_mode( gtk.WRAP_WORD )
        self._text.set_left_margin( self.margin )
        self._text.set_right_margin( self.margin )

        self._sw.add( self._text )
        self._text.show()
        self._diag.vbox.pack_start( self._sw, expand=True, fill=True )
        self._sw.show()
        self.__setup_text__()
    # __setup_gui__()


    def __setup_text__( self ):
        self._buf = self._text.get_buffer()
        self._buf.create_tag( "label", weight=pango.WEIGHT_BOLD )
        self._buf.create_tag( "code", foreground="gray25",
                              family="monospace"  )
        self._buf.create_tag( "exc", foreground="#880000",
                              weight=pango.WEIGHT_BOLD )
    # __setup_text__()


    def show_exception( self, exctype, value, tb ):
        import traceback
        self._exctype.set_text( str( exctype ) )
        self.print_tb( tb )

        lines = traceback.format_exception_only( exctype, value )
        msg = lines[ 0 ]
        print repr( msg )
        result = msg.split( ' ', 1 )
        if len( result ) == 1:
            msg = result[ 0 ]
            arguments = ""
        else:
            msg, arguments = result

        self._insert_text( "\n" )
        self._insert_text( msg, "exc" )
        self._insert_text( " " )
        self._insert_text( arguments )
    # show_exception()


    def save_exception( self, exctype, value, tb ):
        import traceback
        import time
        filename = "%s-%s-%s.tb" % ( sys.argv[ 0 ],
                                  os.getuid(),
                                  int( time.time() ) )
        filename = os.path.join( os.path.sep, "tmp", filename )
        f = open( filename, "wb" )
        try:
            os.chmod( filename, 0600 )
        except:
            pass

        for e in traceback.format_exception( exctype, value, tb ):
            f.write( e )
        f.close()
        self._save_name.set_text( filename )
    # save_exception()


    def print_tb( self, tb, limit=None ):
        import linecache

        if limit is None:
            if hasattr( sys, "tracebacklimit" ):
                limit = sys.tracebacklimit
        n = 0
        while tb is not None and ( limit is None or n < limit ):
            f = tb.tb_frame
            lineno = tb.tb_lineno
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            self._print_file( filename, lineno, name )
            line = linecache.getline( filename, lineno )
            if line:
                self._insert_text( "    " + line.strip() + "\n\n", "code" )
            tb = tb.tb_next
            n = n+1
    # print_tb()


    def _insert_text( self, text, *tags ):
        end_iter = self._buf.get_end_iter()
        self._buf.insert_with_tags_by_name( end_iter, text, *tags )
    # _insert_text()


    def _print_file( self, filename, lineno, name ):
        if filename.startswith( os.getcwd() ):
            filename = filename.replace( self._pwd, '' )[ 1 : ]

        self._insert_text( "File: ", "label" )
        self._insert_text( filename )
        self._insert_text( "\n" )
        self._insert_text( "Line: ", "label" )
        self._insert_text( str( lineno ) )
        self._insert_text( "\n" )
        self._insert_text( "Function: ", "label" )
        self._insert_text( name )
        self._insert_text( "\n" )
    # _print_file()

    def _start_debugger( self ):
        import pdb
        pdb.pm()
    # _start_debugger()



    def run( self, error=None ):
        r = self._diag.run()
        if r == gtk.RESPONSE_CLOSE or gtk.RESPONSE_DELETE_EVENT:
            raise SystemExit( error )
    # run()


    def except_hook( exctype, value, tb ):
        if exctype is not KeyboardInterrupt:
            d = DebugDialog()
            d.save_exception( exctype, value, tb )
            d.show_exception( exctype, value, tb )
            d.run()
            d.destroy()

        raise SystemExit
    # except_hook()
    except_hook = staticmethod( except_hook )
# DebugDialog
sys.excepthook = DebugDialog.except_hook


class _EGWidLabelEntry( _EGDataWidget ):
    """Widget that holds a label and an associated Entry.

    @note: _EGWidLabelEntry must B{NOT} be used directly! You should use
    a widget that specialize this instead.

    @attention: B{Widget Developers:} You must setup an instance attribute
    C{_entry} before using it, since this will be set as mnemonic for this
    label and also returned in L{__get_widgets__}().
    """
    label = _gen_ro_property( "label" )

    def __init__( self, id, persistent, label="" ):
        _EGDataWidget.__init__( self, id, persistent )
        self.label = label or id
        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        self._label = gtk.Label( self.label )
        self._label.set_justify( gtk.JUSTIFY_RIGHT )
        self._label.set_alignment( xalign=1.0, yalign=0.5 )
        self._label.set_mnemonic_widget( self._entry )
        self._widgets = ( self._label, self._entry )
    # __setup_gui__()


    def get_value( self ):
        return self._entry.get_value()
    # get_value()


    def set_value( self, value ):
        self._entry.set_value( value )
    # set_value()


    def __str__( self ):
        return "%s( id=%r, label=%r, value=%r )" % \
               ( self.__class__.__name__, self.id, self.label,
                 self.get_value() )
    # __str__()
    __repr__ = __str__
# _EGWidLabelEntry


class App( _EGObject, AutoGenId ):
    """An application window.

    This is the base of Eagle programs, since it will hold every graphical
    component.

    An App window is split in 5 areas:
     - left
     - right
     - center
     - top
     - bottom
    the first 3 have a vertical layout, the other have horizontal layout.
    Every area has its own scroll bars that are shown automatically when
    need.

    Also provided is an extra area, that is shown in another window. This is
    the preferences area. It have a vertical layout and components that
    hold data are made persistent automatically. You should use
    L{PreferencesButton} to show this area.

    Extra information like author, description, help, version, license and
    copyright are used in specialized dialogs. You may show these dialogs
    with L{AboutButton} and L{HelpButton}.

    Widgets can be reach with L{get_widget_by_id}, example:
       >>> app = App( "My App", left=Entry( id="entry" ) )
       >>> app.get_widget_by_id( "entry" )
       Entry( id='entry', label='entry', value='' )

    You may also reach widgets using dict-like syntax, but with the
    special case for widgets that hold data, these will be provided
    using their L{set_data<_EGDataWidget.set_data>} and
    L{get_data<_EGDataWidget.get_data>}, it make things easier, but
    B{be careful to don't misuse it!}. Example:

       >>> app= App( "My App", left=Entry( id="entry" ),
       ...           right=Canvas( "canvas", 300, 300 ) )
       >>> app[ "entry" ]
       ''
       >>> app[ "entry" ] = "text"
       >>> app[ "entry" ]
       'text'
       >>> app[ "canvas" ]
       Canvas( id='canvas', width=300, height=300, label='' )
       >>> app[ "canvas" ].draw_text( "hello" )
       >>> app[ "entry" ].get_value() # will fail, since it's a data widget

    """
    border_width = 10
    spacing = 3

    title = _gen_ro_property( "title" )
    left = _gen_ro_property( "left" )
    right = _gen_ro_property( "right" )
    top = _gen_ro_property( "top" )
    bottom = _gen_ro_property( "bottom" )
    center = _gen_ro_property( "center" )
    preferences = _gen_ro_property( "preferences" )
    _widgets = _gen_ro_property( "_widgets" )

    def __init__( self, title, id=None,
                  center=None, left=None, right=None, top=None, bottom=None,
                  preferences=None,
                  quit_callback=None, data_changed_callback=None,
                  author=None, description=None, help=None, version=None,
                  license=None, copyright=None ):
        """App Constructor.

        @param title: application name, to be displayed in the title bar.
        @param id: unique id to this application, or None to generate one
               automatically.
        @param center: list of widgets to be laid out vertically in the
               window's center.
        @param left: list of widgets to be laid out vertically in the
               window's left side.
        @param right: list of widgets to be laid out vertically in the
               window's right side.
        @param top: list of widgets to be laid out horizontally in the
               window's top.
        @param bottom: list of widgets to be laid out horizontally in the
               window's bottom.
        @param preferences: list of widgets to be laid out vertically in
               another window, this can be shown with L{PreferencesButton}.
        @param author: the application author or list of author, used in
               L{AboutDialog}, this can be shown with L{AboutButton}.
        @param description: application description, used in L{AboutDialog}.
        @param help: help text, used in L{AboutDialog} and L{HelpDialog}, this
               can be shown with L{HelpButton}.
        @param version: application version, used in L{AboutDialog}.
        @param license: application license, used in L{AboutDialog}.
        @param copyright: application copyright, used in L{AboutDialog}.
        @param quit_callback: function (or list of functions) that will be
               called when application is closed. Function will receive as
               parameter the reference to App.
        @param data_changed_callback: function (or list of functions) that will
               be called when some widget that holds data have its data
               changed. Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        """
        _EGObject.__init__( self, id )
        self.title = title
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.center = center
        self.preferences = preferences
        self.author = _str_tuple( author )
        self.description = _str_tuple( description )
        self.help = _str_tuple( help )
        self.version = _str_tuple( version )
        self.license = _str_tuple( license )
        self.copyright = _str_tuple( copyright )
        self._widgets = {}

        self.quit_callback = _callback_tuple( quit_callback )
        self.data_changed_callback = _callback_tuple( data_changed_callback )

        self.__add_to_app_list__()
        self.__setup_gui__()
        self.__setup_connections__()
        self.load()
    # __init__()


    def __getitem__( self, name ):
        w = self.get_widget_by_id( name )
        if isinstance( w, _EGDataWidget ):
            return w.get_value()
        else:
            return w
    # __getitem__()


    def __setitem__( self, name, value ):
        w = self.get_widget_by_id( name )
        if isinstance( w, _EGDataWidget ):
            return w.set_value( value )
        else:
            raise TypeError(
                "Could not set value of widget '%s' of type '%s'." % \
                ( name, type( w ).__name__ ) )
    # __setitem__()


    def get_widget_by_id( self, widget_id ):
        """Return referece to widget with provided id or None if not found."""
        if isinstance( widget_id, _EGWidget ) and \
           widget_id in self._widgets.itervalues():
            return widget_id
        else:
            return self._widgets.get( widget_id, None )
    # get_widget_by_id()


    def show_about_dialog( self ):
        """Show L{AboutDialog} of this App."""
        diag = AboutDialog( app=self,
                            title=self.title,
                            author=self.author,
                            description=self.description,
                            help=self.help,
                            version=self.version,
                            license=self.license,
                            copyright=self.copyright,
                            )
        diag.run()
    # show_about_dialog()


    def show_help_dialog( self ):
        """Show L{HelpDialog} of this App."""
        diag = HelpDialog( app=self,
                           title=self.title,
                           help=self.help,
                           )
        diag.run()
    # show_help_dialog()


    def file_chooser( self, action, filename=None,
                      filter=None, multiple=False ):
        """Show L{FileChooser} and return selected file(s).

        @param action: must be one of ACTION_* as defined in L{FileChooser}.
        @param filter: a pattern (ie: '*.png'), mime type or a list.

        @see: L{FileChooser}
        """
        diag = FileChooser( app=self, action=action,
                            filename=filename, filter=filter,
                            multiple=multiple )
        return diag.run()
    # file_chooser()


    def show_preferences_dialog( self ):
        """Show L{PreferencesDialog} associated with this App."""
        return self._preferences.run()
    # show_preferences_dialog()


    def __get_window__( self ):
        return self._win
    # __get_window__()


    def __add_to_app_list__( self ):
        if not self.id:
            self.id = self.__get_id__()

        if self.id in _apps:
            raise ValueError( "App id '%s' already existent!" % self.id )

        _apps[ self.id ] = self
    # __add_to_app_list__()


    def __add_widget__( self, widget ):
        if widget.id in self._widgets:
            w = self._widgets[ widget.id ]
            raise ValueError( ( "Object id \"%s\" (type: %s) already in "
                                "application \"%s\" as type: %s!" ) % \
                              ( widget.id,
                                widget.__class__.__name__,
                                self.id,
                                w.__class__.__name__ ) )
        else:
            if widget.app is None:
                self._widgets[ widget.id ] = widget
                widget.app = self
            elif widget.app != self:
                try:
                    id = widget.app.id
                except:
                    id = widget.app
                raise ValueError( ( "Object \"%s\" already is in another "
                                    "App: \"%s\"" ) % \
                                  ( widget.id, id ) )
    # __add_widget__()


    def __setup_gui__( self ):
        self._win = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self._win.set_name( self.id )
        self._win.set_title( self.title )
        self._win.set_default_size( 800, 600 )
        self._win.set_border_width( self.border_width )

        self._hbox = gtk.HBox( False, self.spacing )
        self._win.add( self._hbox )

        self.__setup_gui_left__()
        self.__setup_gui_right__()
        self.__setup_gui_center__()
        self.__setup_gui_top__()
        self.__setup_gui_bottom__()
        self.__setup_gui_preferences__()

        self._vbox = gtk.VBox( False, self.spacing )

        if self._top.__get_widgets__():
            self._vbox.pack_start( self._top, expand=False, fill=True )
            if self._center.__get_widgets__() or \
               self._bottom.__get_widgets__():
                self._vbox.pack_start( gtk.HSeparator(), expand=False,
                                       fill=True )

        if self._center.__get_widgets__():
            self._vbox.pack_start( self._center, expand=True, fill=True )

        if self._bottom.__get_widgets__():
            if self._center.__get_widgets__():
                self._vbox.pack_start( gtk.HSeparator(), expand=False,
                                       fill=True )
            self._vbox.pack_start( self._bottom, expand=False, fill=True )

        if self._left.__get_widgets__():
            self._hbox.pack_start( self._left,  expand=False, fill=True )
            if self._center.__get_widgets__() or self._top.__get_widgets__ or \
               self._bottom.__get_widgets__() or self._right.__get_widgets__():
                self._hbox.pack_start( gtk.VSeparator(),
                                       expand=False, fill=False )

        self._hbox.pack_start( self._vbox,  expand=True, fill=True )

        if self._right.__get_widgets__():
            if self._center.__get_widgets__() or self._top.__get_widgets__ or \
               self._bottom.__get_widgets__():
                self._hbox.pack_start( gtk.VSeparator(),
                                       expand=False, fill=False )
            self._hbox.pack_end( self._right, expand=False, fill=True )

        self._win.show_all()
    # __setup_gui__()


    def __setup_gui_left__( self ):
        self._left = _VPanel( self, id="left", children=self.left )
    # __setup_gui_left__()


    def __setup_gui_right__( self ):
        self._right =_VPanel( self, id="right", children=self.right )
    # __setup_gui_right__()


    def __setup_gui_center__( self ):
        self._center = _VPanel( self, id="center", children=self.center )
    # __setup_gui_center__()


    def __setup_gui_top__( self ):
        self._top = _HPanel( self, id="top", children=self.top )
    # __setup_gui_top__()


    def __setup_gui_bottom__( self ):
        self._bottom = _HPanel( self, id="bottom", children=self.bottom )
    # __setup_gui_bottom__()


    def __setup_gui_preferences__( self ):
        self._preferences = PreferencesDialog( self,
                                               children=self.preferences )
    # __setup_gui_preferences__()


    def __setup_connections__( self ):
        self._win.connect( "delete_event", self.__delete_event__ )
    # __setup_connections__()


    def data_changed( self, widget, value ):
        """Notify that widget changed it's value.

        Probably you will not need to call this directly.
        """
        self.save()
        for c in self.data_changed_callback:
            c( self, widget, value )
    # data_changed()


    def __delete_event__( self, *args ):
        self.save()
        for c in self.quit_callback:
            c( self )

        del _apps[ self.id ]
        if not _apps:
            gtk.main_quit()
    # __delete_event__()


    def __persistence_filename__( self ):
        return "%s.save_data" % self.id
    # __persistence_filename__()


    def save( self ):
        """Save data from widgets to file.

        Probably you will not need to call this directly.
        """
        d = {}
        for id, w in self._widgets.iteritems():
            if isinstance( w, _EGDataWidget ) and w.persistent:
                d[ id ] = w.get_value()

        f = open( self.__persistence_filename__(), "wb" )
        pickle.dump( d, f, pickle.HIGHEST_PROTOCOL )
        f.close()
    # save()


    def load( self ):
        """Load data to widgets from file.

        Probably you will not need to call this directly.
        """
        try:
            f = open( self.__persistence_filename__(), "rb" )
        except IOError:
            return

        d = pickle.load( f )
        f.close()

        for id, v in d.iteritems():
            try:
                w = self._widgets[ id ]
            except KeyError:
                w = None
            if isinstance( w, _EGDataWidget ) and w.persistent:
                w.set_value( v )
    # load()


    def close( self ):
        """Close application window."""
        self.__delete_event__()
        self._win.destroy()
    # close()
# App


class Canvas( _EGWidget ):
    """The drawing area.

    Eagle's drawing area (Canvas) is provided with a frame and an optional
    label, together with scrollbars, to make it fit everywhere.

    """
    padding = 5
    bgcolor= "black"

    LEFT = -1
    CENTER = 0
    RIGHT = 1

    FONT_OPTION_BOLD       = 1
    FONT_OPTION_OBLIQUE    = 2
    FONT_OPTION_ITALIC     = 4

    FONT_NAME_NORMAL       = "normal"
    FONT_NAME_SERIF        = "serif"
    FONT_NAME_SANS         = "sans"
    FONT_NAME_MONO         = "monospace"

    label = _gen_ro_property( "label" )

    def __init__( self, id, width, height, label="", bgcolor=None,
                  callback=None ):
        """Canvas Constructor.

        @param id: unique identifier.
        @param width: width of the drawing area in pixels, widget can be
               larger or smaller because and will use scrollbars if need.
        @param height: height of the drawing area in pixels, widget can be
               larger or smaller because and will use scrollbars if need.
        @param label: label to display in the widget frame around the
               drawing area.
        @param bgcolor: color to paint background.
        @param callback: function (or list of functions) to call when
               mouse state changed in the drawing area. Function will get
               as parameters:
                - App reference
                - Canvas reference
                - Button state
                - horizontal positon (x)
                - vertical positon (y)
        """
        _EGWidget.__init__( self, id )
        self.label = label
        self.width = width
        self.height = height

        self._pixmap = None
        self._callback = _callback_tuple( callback )

        # style and color context must be set just after drawing area is
        # attached to a window, otherwise they'll be empty and useless.
        # This is done in configure_event.
        self._style = None
        self._fg_gc_normal = None
        self._bg_gc_normal = None

        if bgcolor is not None:
            self.bgcolor = self.__color_from__( bgcolor )

        self.__setup_gui__( width, height )
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self, width, height ):
        self._frame = gtk.Frame( self.label )
        self._sw = gtk.ScrolledWindow()
        self._area = gtk.DrawingArea()

        self._sw.set_border_width( self.padding )

        self._frame.add( self._sw )
        self._frame.set_shadow_type( gtk.SHADOW_OUT )

        self._area.set_size_request( width, height )
        self._sw.add_with_viewport( self._area )
        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )
        self._sw.show_all()

        self._widgets = ( self._frame, )
    # __setup_gui__()


    def __set_useful_attributes__( self ):
        self._style = self._area.get_style()
        self._fg_gc_normal = self._style.fg_gc[ gtk.STATE_NORMAL ]
        self._bg_gc_normal = self._style.bg_gc[ gtk.STATE_NORMAL ]
    # __set_useful_attributes__()


    def __setup_connections__( self ):
        def configure_event( widget, event ):
            if self._pixmap is None:
                self.__set_useful_attributes__()
                w, h = self._area.size_request()
                self.resize( w, h )
            return True
        # configure_event()
        self._area.connect( "configure_event", configure_event )


        def expose_event( widget, event ):
            x , y, width, height = event.area
            gc = widget.get_style().fg_gc[ gtk.STATE_NORMAL ]
            widget.window.draw_drawable( gc, self._pixmap, x, y, x, y,
                                         width, height )
            return False
        # expose_event()
        self._area.connect( "expose_event", expose_event )


        def button_press_event( widget, event ):
            if self._pixmap != None:
                for c in self._callback:
                    c( self.app, self, event.button,
                       int( event.x ), int( event.y ) )
            return True
        # button_press_event()
        self._area.connect( "button_press_event", button_press_event )


        def motion_notify_event( widget, event ):
            if event.is_hint:
                x, y, state = event.window.get_pointer()
            else:
                x = event.x
                y = event.y
                state = event.state

            if state & gtk.gdk.BUTTON1_MASK and self._pixmap != None:
                for c in self._callback:
                    c( self.app, self, 1, x, y )

            return True
        # motion_notify_event()
        if self._callback:
            self._area.connect( "motion_notify_event", motion_notify_event )


        # Enable events
        self._area.set_events( gtk.gdk.EXPOSURE_MASK |
                               gtk.gdk.LEAVE_NOTIFY_MASK |
                               gtk.gdk.BUTTON_PRESS_MASK |
                               gtk.gdk.POINTER_MOTION_MASK |
                               gtk.gdk.POINTER_MOTION_HINT_MASK )
    # __setup_connections__()


    def __get_resize_mode__( self ):
        return ( gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND )
    # __get_resize_mode__()



    def __color_from__( color ):
        """Convert from color to internal representation.

        Gets a string, integer or tuple/list arguments and converts into
        internal color representation.
        """
        if isinstance( color, str ):
            return gtk.gdk.color_parse( color )
        elif isinstance( color, gtk.gdk.Color ):
            return color

        if isinstance( color, int ):
            r = ( color >> 16 ) & 0xff
            g = ( color >>  8 ) & 0xff
            b = ( color & 0xff )
        elif isinstance( color, ( tuple, list ) ):
            r, g, b = color

        r = int( r / 255.0 * 65535 )
        g = int( g / 255.0 * 65535 )
        b = int( b / 255.0 * 65535 )

        return gtk.gdk.Color( r, g, b )
    # __color_from__()
    __color_from__ = staticmethod( __color_from__ )


    def __configure_gc__( self, fgcolor=None, bgcolor=None, fill=None,
                          line_width=None, line_style=None ):
        if fgcolor is not None:
            fgcolor = self.__color_from__( fgcolor )
        if bgcolor is not None:
            bgcolor = self.__color_from__ ( bgcolor )

        k = {}
        if fill is not None:
            k[ "fill" ] = gtk.gdk.SOLID
        if line_width is not None:
            k[ "line_width" ] = line_width
        if line_style is not None:
            k[ "line_style" ] = line_style

        gc = self._pixmap.new_gc( **k )

        if fgcolor is not None:
            gc.set_rgb_fg_color( fgcolor )
        if bgcolor is not None:
            gc.set_rgb_bg_color( bgcolor )
        return gc
    # __configure_gc__()


    def resize( self, width, height ):
        """Resize the drawing area."""
        old = self._pixmap
        self._pixmap = gtk.gdk.Pixmap( self._area.window, width, height )
        if old is None:
            # Paint with bg color
            self.clear()
        else:
            # copy old contents over this
            w, h = old.get_size()
            self._pixmap.draw_drawable( self._fg_gc_normal, old,
                                        0, 0, 0, 0, w, h )
    # resize()


    def draw_image( self, image, x=0, y=0,
                    width=None, height=None,
                    src_x=0, src_y=0 ):
        """Draw image on canvas.

        By default it draws entire image at top canvas corner.

        You may restrict which image areas to use with src_x, src_y, width
        and height.

        You may choose position on canvas with x and y.
        """
        if not isinstance( image, Image ):
            raise TypeError( ( "image must be instance of Image class, "
                               "but %s found!" ) % ( type( image ).__name__ ) )

        p = image.__get_gtk_pixbuf__()

        if src_x >= p.get_width():
            raise ValueError( "src_x is greater or equal width!" )

        if src_y >= p.get_height():
            raise ValueError( "src_y is greater or equal height!" )

        if width is None or width < 1:
            width = p.get_width()

        if height is None or height < 1:
            height = p.get_height()

        if src_x + width > p.get_width():
            width = p.get_width() - src_x
        if src_y + height > p.get_height():
            height = p.get_height() - src_y

        self._pixmap.draw_pixbuf( self._fg_gc_normal,
                                  p, src_x, src_y, x, y, width, height )
        self._area.queue_draw_area( x, y, width, width )
    # draw_image()


    def draw_text( self, text, x=0, y=0,
                   fgcolor=None, bgcolor=None,
                   font_name=None, font_size=None, font_options=0,
                   width=None, wrap_word=False,
                   alignment=LEFT, justify=True ):
        """Draw text on canvas.

        By default text is draw with current font and colors at top canvas
        corner.

        You may limit width providing a value and choose if it should wrap
        at words (wrap_word=True) or characters (wrap_word=False).


        Colors can be specified with fgcolor an bgcolor. If not provided, the
        system foreground color is used and no background color is used.

        Font name, size and options may be specified using font_name,
        font_size and font_options, respectively. Try to avoid using
        system specific font fames, use those provided by FONT_NAME_*.
        Font options is OR'ed values from FONT_OPTIONS_*.

        Text alignment is one of LEFT, RIGHT or CENTER.
        """
        if fgcolor is not None:
            fgcolor = self.__color_from__( fgcolor )
        if bgcolor is not None:
            bgcolor = self.__color_from__( bgcolor )

        layout = self._area.create_pango_layout( text )
        if width is not None:
            layout.set_width( width * pango.SCALE )
            if wrap_word:
                layout.set_wrap( pango.WRAP_WORD )

        layout.set_justify( justify )
        alignment = { self.LEFT: pango.ALIGN_LEFT,
                      self.CENTER: pango.ALIGN_CENTER,
                      self.RIGHT: pango.ALIGN_RIGHT }.get( alignment,
                                                           pango.ALIGN_CENTER )
        layout.set_alignment( alignment )

        if font_name or font_size or font_options:
            ctx = layout.get_context()
            fd = layout.get_context().get_font_description()
            if font_name:
                fd.set_family( font_name )
            if font_size:
                fd.set_size( font_size * pango.SCALE)
            if font_options:
                if font_options & self.FONT_OPTION_BOLD:
                    fd.set_weight( pango.WEIGHT_BOLD )
                if font_options & self.FONT_OPTION_ITALIC:
                    fd.set_style( pango.STYLE_ITALIC )
                if font_options & self.FONT_OPTION_OBLIQUE:
                    fd.set_style( pango.STYLE_OBLIQUE )
            layout.set_font_description( fd )

        self._pixmap.draw_layout( self._fg_gc_normal, x, y, layout,
                                  fgcolor, bgcolor )
        w, h = layout.get_pixel_size()
        self._area.queue_draw_area( x, y, w, h )
    # draw_text()



    def draw_point( self, x, y, color=None ):
        """Draw point."""
        gc = self.__configure_gc__( fgcolor=color )
        self._pixmap.draw_point( gc, x, y )
        self._area.queue_draw_area( x, y, 1, 1 )
    # draw_point()


    def draw_points( self, points, color=None ):
        """Draw points.

        Efficient way to draw more than one point with the same
        characteristics.
        """
        gc = self.__configure_gc__( fgcolor=color )
        self._pixmap.draw_points( gc, points )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_poinst()


    def draw_line( self, x0, y0, x1, y1, color=None, size=1 ):
        """Draw line."""
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_line( gc, x0, y0, x1, y1 )

        w, h = abs( x1 - x0 ) + 1, abs( y1 - y0 ) + 1
        x, y = min( x0, x1 ), min( y0, y1 )
        self._area.queue_draw_area( x, y, w, h )
    # draw_line()


    def draw_segments( self, segments, color=None, size=1 ):
        """Draw line segments.

        Efficient way to draw more than one line with the same
        characteristics.

        Lines are not connected, use L{draw_lines} instead.
        """
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_segments( gc, segments )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_segments()


    def draw_lines( self, points, color=None, size=1 ):
        """Draw lines connecting points.

        Points are connected using lines, but first and last points
        are not connected, use L{draw_polygon} instead.
        """
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_lines( gc, points )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_lines()


    def draw_rectangle( self, x, y, width, height, color=None, size=1,
                        fillcolor=None, filled=False ):
        """Draw rectagle.

        If L{filled} is C{True}, it will be filled with L{fillcolor}.

        If L{color} is provided, it will draw the rectangle's frame, even
        if L{filled} is C{True}.
        """
        if filled:
            gc = self.__configure_gc__( fgcolor=fillcolor, fill=filled )
            self._pixmap.draw_rectangle( gc, True, x, y, width, height )

        if size > 0:
            gc = self.__configure_gc__( fgcolor=color, line_width=size )
            self._pixmap.draw_rectangle( gc, False, x, y, width, height )
        else:
            size = 0

        half = size / 2
        self._area.queue_draw_area( x-half, y-half, width+size, height+size )
    # draw_rectangle()


    def draw_arc( self, x, y, width, height, start_angle, end_angle,
                  color=None, size=1, fillcolor=None, filled=False ):
        """Draw arc on canvas.

        Arc will be the part of an ellipse that starts at ( L{x}, L{y} )
        and have size of L{width}xL{height}.

        L{start_angle} and L{end_angle} are in radians, starts from the
        positive x-axis and are counter-clockwise.

        If L{filled} is C{True}, it will be filled with L{fillcolor}.

        If L{color} is provided, it will draw the arc's frame, even
        if L{filled} is C{True}. Frame here is just the curve, not the
        straight lines that are limited by L{start_angle} and L{end_angle}.
        """
        # GTK: angles are in 1/64 of degree and must be integers
        mult = 180.0 / 3.1415926535897931 * 64.0
        start_angle = int( mult * start_angle )
        end_angle = int( mult * end_angle )

        if filled:
            gc = self.__configure_gc__( fgcolor=fillcolor, fill=filled )
            self._pixmap.draw_arc( gc, True, x, y, width, height,
                                   start_angle, end_angle )
        if size > 0:
            gc = self.__configure_gc__( fgcolor=color, line_width=size )
            self._pixmap.draw_arc( gc, False, x, y, width, height,
                                   start_angle, end_angle )
        else:
            size = 0

        half = size / 2
        self._area.queue_draw_area( x-half, y-half, width+size, height+size )
    # draw_arc()


    def draw_polygon( self, points, color=None, size=1,
                      fillcolor=None, filled=False ):
        """Draw polygon on canvas.

        If L{filled} is C{True}, it will be filled with L{fillcolor}.

        If L{color} is provided, it will draw the polygon's frame, even
        if L{filled} is C{True}.
        """
        if filled:
            gc = self.__configure_gc__( fgcolor=fillcolor, fill=filled )
            self._pixmap.draw_polygon( gc, True, points )

        if size > 0:
            gc = self.__configure_gc__( fgcolor=color, line_width=size )
            self._pixmap.draw_polygon( gc, False, points )
        else:
            size = 0

        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_polygon()


    def clear( self ):
        """Clear using bgcolor."""
        self.fill( self.bgcolor )
    # clear()


    def fill( self, color ):
        w, h = self.get_size()
        self.draw_rectangle( 0, 0, w, h, color, size=0, fillcolor=color,
                             filled=True )
    # fill()


    def get_size( self ):
        return self._pixmap.get_size()
    # get_size()


    def get_image( self ):
        """Get the L{Image} that represents this drawing area."""
        w, h = self._pixmap.get_size()
        img = gtk.gdk.Pixbuf( gtk.gdk.COLORSPACE_RGB, True, 8, w, h )
        img.get_from_drawable( self._pixmap, self._area.get_colormap(),
                               0, 0, 0, 0, w, h )
        return Image( __int_image__=img )
    # get_image()


    def __str__( self ):
        return "%s( id=%r, width=%r, height=%r, label=%r )" % \
               ( self.__class__.__name__, self.id, self.width, self.height,
                 self.label )
    # __str__()
    __repr__ = __str__
# Canvas


class Entry( _EGWidLabelEntry ):
    """Text entry.

    The simplest user input component. Its contents are free-form and not
    filtered/masked.
    """
    value = _gen_ro_property( "value" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", value="", callback=None,
                  persistent=False ):
        """Entry constructor.

        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.value = value
        self.callback = _callback_tuple( callback )

        _EGWidLabelEntry.__init__( self, id, persistent, label )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._entry = gtk.Entry()
        self._entry.set_name( self.id )
        self._entry.set_text( self.value )

        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._entry.connect( "changed", callback )
    # __setup_connections__()


    def get_value( self ):
        return self._entry.get_text()
    # get_value()


    def set_value( self, value ):
        self._entry.set_text( str( value ) )
    # set_value()
# Entry


class Password( Entry ):
    """Password entry.

    Like L{Entry}, but will show '*' instead of typed chars.
    """
    def __init__( self, id, label="", value="", callback=None,
                  persistent=False ):
        """Password constructor.

        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        Entry.__init__( self, id, label, value, callback, persistent )
        self._entry.set_visibility( False )
    # __init__()
# Password


class Spin( _EGWidLabelEntry ):
    """Spin button entry.

    Spin buttons are numeric user input that checks if value is inside
    a specified range. It also provides small buttons to help incrementing/
    decrementing value.
    """
    value = _gen_ro_property( "value" )
    min = _gen_ro_property( "min" )
    max = _gen_ro_property( "max" )
    step = _gen_ro_property( "step" )
    digits = _gen_ro_property( "digits" )

    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None, digits=3,
                  callback=None, persistent=False ):
        """Spin constructor.

        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value.
        @param max: maximum value.
        @param step: step to use to decrement/increment using buttons.
        @param digits: how many digits to show.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.digits = digits
        self.callback = _callback_tuple( callback )

        _EGWidLabelEntry.__init__( self, id, persistent, label )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        k = {}

        if self.value is not None:
            k[ "value" ] = self.value

        if self.min is not None:
            k[ "lower" ] = self.min

        if self.max is not None:
            k[ "upper" ] = self.max

        if self.step is not None:
            k[ "step_incr" ] = self.step

        adj = gtk.Adjustment( **k )
        self._entry = gtk.SpinButton( adjustment=adj, digits=self.digits )
        self._entry.set_name( self.id )
        self._entry.set_numeric( True )
        self._entry.set_snap_to_ticks( False )

        if self.step is not None:
            self._entry.set_increments( self.step / 2, self.step * 2 )

        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._entry.connect( "value-changed", callback )
    # __setup_connections__()


    def set_value( self, value ):
        self._entry.set_value( float( value ) )
    # set_value()
# Spin


class IntSpin( Spin ):
    """Integer-only Spin button.

    Convenience widget that behaves like L{Spin} with digits set to
    zero and also ensure L{set_value} and L{get_value} operates on
    integers.
    """
    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None,
                  callback=None, persistent=False ):
        """Integer Spin constructor.

        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value.
        @param max: maximum value.
        @param step: step to use to decrement/increment using buttons.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        if value is not None:
            value = int( value )
        if min is not None:
            min = int( min )
        if max is not None:
            max = int( max )
        if step is not None:
            step = int( step )
        Spin.__init__( self, id, label, value, min, max, step, 0, callback,
                       persistent )
    # __init__()


    def get_value( self ):
        return int( Spin.get_value( self ) )
    # get_value()


    def set_value( self, value ):
        Spin.set_value( self, int( value ) )
    # set_value()
# IntSpin


class UIntSpin( IntSpin ):
    """Unsigned integer-only Spin button.

    Convenience widget that behaves like L{IntSpin} with minimum value
    always greater or equal zero.
    """
    def __init__( self, id, label="",
                  value=None, min=0, max=None, step=None,
                  callback=None, persistent=False ):
        """Unsigned Integer Spin constructor.

        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value, must be greater or equal zero.
        @param max: maximum value.
        @param step: step to use to decrement/increment using buttons.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        if min < 0:
            raise ValueError( "UIntSpin cannot have min < 0!" )
        Spin.__init__( self, id, label, value, min, max, step, 0, callback,
                       persistent )
    # __init__()
# UIntSpin


class Color( _EGWidLabelEntry ):
    """Button to select colors.

    It show current/last selected color and may pop-up a new dialog to
    select a new one.
    """
    color = _gen_ro_property( "color" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", color=0, callback=None,
                  persistent=False ):
        """Color selector constructor.

        @param label: what to show on a label on the left side of the widget.
        @param color: initial content. May be a triple with elements within
               the range 0-255, an string with color in HTML format or even
               a color present in X11's rgb.txt.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.color = self.color_from( color )
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label )

        self.__setup_connections__()
    # __init__()


    def color_from( color ):
        if isinstance( color, str ):
            return gtk.gdk.color_parse( color )

        if isinstance( color, int ):
            r = ( color >> 16 ) & 0xff
            g = ( color >>  8 ) & 0xff
            b = ( color & 0xff )
        elif isinstance( color, ( tuple, list ) ):
            r, g, b = color

        r = int( r / 255.0 * 65535 )
        g = int( g / 255.0 * 65535 )
        b = int( b / 255.0 * 65535 )

        return gtk.gdk.Color( r, g, b )
    # color_from()
    color_from = staticmethod( color_from )


    def __setup_gui__( self ):
        self._entry = gtk.ColorButton( self.color )
        self._entry.set_name( self.id )
        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._entry.connect( "color-set", callback )
    # __setup_connections__()


    def get_value( self ):
        """Return a tuple with ( red, green, blue ), each in 0-255 range."""
        c = self._entry.get_color()
        r = int( c.red   / 65535.0 * 255 )
        g = int( c.green / 65535.0 * 255 )
        b = int( c.blue  / 65535.0 * 255 )
        return ( r, g, b )
    # get_value()


    def set_value( self, value ):
        """
        @param value: May be a triple with elements within
               the range 0-255, an string with color in HTML format or even
               a color present in X11's rgb.txt.
        """
        self._entry.set_color( self.color_from( value ) )
    # set_value()
# Color


class Font( _EGWidLabelEntry ):
    """Button to select fonts.

    It show current/last selected font and may pop-up a new dialog to
    select a new one.
    """
    font = _gen_ro_property( "font" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", font="sans 12", callback=None,
                  persistent=False ):
        """Font selector constructor.

        @param label: what to show on a label on the left side of the widget.
        @param font: initial content.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.font = font
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label )

        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._entry = gtk.FontButton( self.font )
        self._entry.set_name( self.id )
        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._entry.connect( "font-set", callback )
    # __setup_connections__()


    def get_value( self ):
        return self._entry.get_font_name()
    # get_value()


    def set_value( self, value ):
        self._entry.set_font_name( value )
    # set_value()
# Font


class Selection( _EGWidLabelEntry ):
    """Selection box (aka Combo box).

    Selection or combo box is an element that allow you to select one of
    various pre-defined values.
    """
    options = _gen_ro_property( "options" )
    active = _gen_ro_property( "active" )

    def __init__( self, id, label="", options=None, active=None,
                  callback=None, persistent=False ):
        """Selection constructor.

        @param label: what to show on a label on the left side of the widget.
        @param options: list of possible values.
        @param active: selected element.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.options = options or []
        self.active  = active
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label )

        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._entry = gtk.combo_box_new_text()
        self._entry.set_name( self.id )
        for i, o in enumerate( self.options ):
            self._entry.append_text( str( o ) )
            if self.active == o:
                self._entry.set_active( i )

        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._entry.connect( "changed", callback )
    # __setup_connections__()


    def get_value( self ):
        return self._entry.get_active_text()
    # get_value()


    def set_value( self, value ):
        for i, o in enumerate( self._entry.get_model() ):
            if o[ 0 ] == value:
                self._entry.set_active( i )
    # set_value()
# Selection


class Progress( _EGWidLabelEntry ):
    """Progress bar."""
    value = _gen_ro_property( "value" )

    def __init__( self, id, label="", value=0.0 ):
        """Progress bar constructor.

        0 <= value <= 1.0
        """
        self.value = value
        _EGWidLabelEntry.__init__( self, id, False, label )
    # __init__()

    def __setup_gui__( self ):
        self._entry = gtk.ProgressBar()
        self._entry.set_name( self.id )
        self.set_value( self.value )
        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def get_value( self ):
        return self._entry.get_fraction()
    # get_value()


    def set_value( self, value ):
        if 1.0 < value <= 100.0:
            value /= 100.0
        elif not ( 0.0 <= value <= 1.0 ):
            raise ValueError( ( "Progress value of \"%s\" must be "
                                "between 0.0 and 1.0!" ) % self.id )
        self._entry.set_fraction( value )
        self._entry.set_text( "%d%%" % ( int( value * 100 ), ) )
    # set_value()


    def pulse( self ):
        """Animate progress bar."""
        self._entry.pulse()
    # pulse()
# Progress


class CheckBox( _EGDataWidget ):
    """Check box.

    Check box is an component that have only two values: True (checked) or
    False (unchecked).
    """
    state = _gen_ro_property( "state" )

    def __init__( self, id, label="", state=False, callback=None,
                  persistent=False ):
        """Check box constructor.

        @param label: what to show on a label on the left side of the widget.
        @param state: initial state.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        """
        self.label = label
        self.state = state
        self.callback = _callback_tuple( callback )

        _EGDataWidget.__init__( self, id, persistent )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._wid = gtk.CheckButton( self.label )
        self._wid.set_name( self.id )
        self._wid.set_active( self.state )
        self._widgets = ( self._wid, )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            v = self.get_value()
            self.app.data_changed( self, v )
            for c in self.callback:
                c( self.app, self, v )
        # callback()
        self._wid.connect( "toggled", callback )
    # __setup_connections__()


    def get_value( self ):
        return self._wid.get_active()
    # get_value()
# CheckBox


class Group( _EGWidget ):
    """Group of various components.

    Group is a component that holds other components, always in a vertical
    layout.

    Group has a frame and may show a label.
    """
    children = _gen_ro_property( "children" )

    def _get_app( self ):
        try:
            return self.__ro_app
        except AttributeError:
            return None
    # _get_app()

    def _set_app( self, value ):
        # We need to overload app setter in order to add
        # children widgets to application as soon as we know the app
        try:
            v = self.__ro_app
        except AttributeError:
            v = None
        if v is None:
            self.__ro_app = value
            self.__add_widgets_to_app__()
        else:
            raise Exception( "Read Only property 'app'." )
    # _set_app()
    app = property( _get_app, _set_app )


    def __init__( self, id, label="", children=None ):
        """Group constructor.

        @param id: unique identified.
        @param label: displayed at top-left.
        @param children: a list of eagle widgets that this group contains.
               They're presented in vertical layout.
        """
        _EGWidget.__init__( self, id )
        self.label = label
        self.children = children or tuple()

        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        self._frame = gtk.Frame( self.label )
        self._frame.set_name( self.id )
        self._contents = _Table( id=( "%s-contents" % self.id ),
                                 children=self.children )
        self._frame.add( self._contents )
        self._widgets = ( self._frame, )
    # __setup_gui__()


    def __add_widgets_to_app__( self ):
        for w in self.children:
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()
# Group


class Button( _EGWidget ):
    """A push button.
    """
    stock = _gen_ro_property( "stock" )
    callback = _gen_ro_property( "callback" )

    stock_items = (
        "about",
        "help",
        "quit",
        "add",
        "remove",
        "refresh",
        "update",
        "yes",
        "no",
        "zoom_100",
        "zoom_in",
        "zoom_out",
        "zoom_fit",
        "undo",
        "execute",
        "stop",
        "open",
        "save",
        "save_as",
        "properties",
        "preferences",
        "print",
        "print_preview",
        "ok",
        "cancel",
        "apply",
        "close",
        "clear",
        "convert",
        "next",
        "back",
        "up",
        "down",
        "font",
        "color",
        )


    _gtk_stock_map = {
        "about": gtk.STOCK_ABOUT,
        "help": gtk.STOCK_HELP,
        "quit": gtk.STOCK_QUIT,
        "add": gtk.STOCK_ADD,
        "remove": gtk.STOCK_REMOVE,
        "refresh": gtk.STOCK_REFRESH,
        "update": gtk.STOCK_REFRESH,
        "yes": gtk.STOCK_YES,
        "no": gtk.STOCK_NO,
        "zoom_100": gtk.STOCK_ZOOM_100,
        "zoom_in": gtk.STOCK_ZOOM_IN,
        "zoom_out": gtk.STOCK_ZOOM_OUT,
        "zoom_fit": gtk.STOCK_ZOOM_FIT,
        "undo": gtk.STOCK_UNDO,
        "execute": gtk.STOCK_EXECUTE,
        "stop": gtk.STOCK_STOP,
        "open": gtk.STOCK_OPEN,
        "save": gtk.STOCK_SAVE,
        "save_as": gtk.STOCK_SAVE_AS,
        "properties": gtk.STOCK_PROPERTIES,
        "preferences": gtk.STOCK_PREFERENCES,
        "print": gtk.STOCK_PRINT,
        "print_preview": gtk.STOCK_PRINT_PREVIEW,
        "ok": gtk.STOCK_OK,
        "cancel": gtk.STOCK_CANCEL,
        "apply": gtk.STOCK_APPLY,
        "close": gtk.STOCK_CLOSE,
        "clear": gtk.STOCK_CLEAR,
        "convert": gtk.STOCK_CONVERT,
        "next": gtk.STOCK_GO_FORWARD,
        "back": gtk.STOCK_GO_BACK,
        "up": gtk.STOCK_GO_UP,
        "down": gtk.STOCK_GO_DOWN,
        "font": gtk.STOCK_SELECT_FONT,
        "color": gtk.STOCK_SELECT_COLOR,
        }

    def __init__( self, id, label="", stock=None, callback=None ):
        """Push button constructor.

        @param label: what text to show, if stock isn't provided.
        @param stock: optional. One of L{stock_items}.
        @param callback: the function (or list of functions) to call
               when button is pressed. Function will get as parameter:
                - App reference
                - Button reference
        """
        self.label = label
        self.stock = stock
        self.callback = _callback_tuple( callback )

        # Check if provided stock items are implemented
        for i in self.stock_items:
            if i not in self._gtk_stock_map:
                print >> sys.stderr, \
                      "Stock item %s missing in implementation map!" % ( i, )

        _EGWidget.__init__( self, id )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        k = {}
        try:
            k[ "stock" ] = self._gtk_stock_map[ self.stock ]
        except KeyError:
            k[ "label" ] = self.label or self.stock

        self._button = gtk.Button( **k )
        self._button.set_name( self.id )
        self._widgets = ( self._button, )
    # __setup_gui__()


    def __setup_connections__( self ):
        def callback( obj ):
            for c in self.callback:
                c( self.app, self )
        # callback()
        self._button.connect( "clicked", callback )
    # __setup_connections__()
# Button


class AboutButton( Button, AutoGenId ):
    """Push button to show L{AboutDialog} of L{App}."""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        def show_about( app_id, wid_id ):
            self.app.show_about_dialog()
        # show_about()
        Button.__init__( self, id or self.__get_id__(),
                         stock="about", callback=show_about )
    # __init__()
# AboutButton


class CloseButton( Button, AutoGenId ):
    """Push button to close L{App}."""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        def close( app_id, wid_id ):
            self.app.close()
        # close()
        Button.__init__( self, id or self.__get_id__(),
                         stock="close", callback=close )
    # __init__()
# CloseButton


class QuitButton( Button, AutoGenId ):
    """Push button to quit all L{App}s."""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        def c( app_id, wid_id ):
            quit()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="quit", callback=c )
    # __init__()
# QuitButton


class HelpButton( Button, AutoGenId ):
    """Push button to show L{HelpDialog} of L{App}."""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        def c( app_id, wid_id ):
            self.app.show_help_dialog()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="help", callback=c )
    # __init__()
# HelpButton


class OpenFileButton( Button, AutoGenId ):
    """Push button to show dialog to choose an existing file."""
    def __init__( self, id=None,
                  filter=None, multiple=False,
                  callback=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param filter: filter files to show, see L{FileChooser}.
        @param multiple: enable selection of multiple files.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - file name or file list (if multiple).

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_OPEN,
                                       filter=filter, multiple=multiple )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c )
    # __init__()
# OpenFileButton


class SelectFolderButton( Button, AutoGenId ):
    """Push button to show dialog to choose an existing folder/directory."""
    def __init__( self, id=None, callback=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - directory/folder name.

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_SELECT_FOLDER )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c )
    # __init__()
# SelectFolderButton


class SaveFileButton( Button, AutoGenId ):
    """Push button to show dialog to choose a file to save."""
    def __init__( self, id=None, filename=None,
                  filter=None, callback=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param filename: default filename.
        @param filter: filter files to show, see L{FileChooser}.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - file name.

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_SAVE,
                                       filename=filename,
                                       filter=filter )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="save", callback=c )
    # __init__()
# SaveFileButton


class PreferencesButton( Button, AutoGenId ):
    """Push button to show L{PreferencesDialog} of L{App}."""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        def c( app_id, wid_id ):
            f = self.app.show_preferences_dialog()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="preferences", callback=c )
    # __init__()
# PreferencesButton


class HSeparator( _EGWidget, AutoGenId ):
    """Horizontal separator"""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        _EGWidget.__init__( self, id or self.__get_id__() )
        self._wid = gtk.HSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# HSeparator


class VSeparator( _EGWidget ):
    """Horizontal separator"""
    def __init__( self, id=None ):
        """You may not provide id, it will be generated automatically"""
        _EGWidget.__init__( self, id or self.__get_id__() )
        self._wid = gtk.VSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# VSeparator


class Label( _EGWidget, AutoGenId ):
    """Text label"""
    label = _gen_ro_property( "label" )

    LEFT   = 0.0
    RIGHT  = 1.0
    CENTER = 0.5
    TOP    = 0.0
    MIDDLE = 0.5
    BOTTOM = 1.0

    def __init__( self, id=None, label="",
                  halignment=LEFT, valignment=MIDDLE ):
        """Label constructor.

        @param id: may not be provided, it will be generated automatically.
        @param label: what this label will show.
        @param halignment: horizontal alignment, like L{LEFT}, L{RIGHT} or
               L{CENTER}.
        @param valignment: vertical alignment, like L{TOP}, L{BOTTOM} or
               L{MIDDLE}.
        """
        _EGWidget.__init__( self, id or self.__get_id__() )
        self.label = label

        self._wid = gtk.Label( self.label )
        self._wid.set_name( self.id )
        self._wid.set_alignment( xalign=halignment, yalign=valignment )
        self._widgets = ( self._wid, )
    # __init__()


    def get_value( self ):
        self._wid.get_text()
    # get_value()


    def set_value( self, value ):
        self._wid.set_text( str( value ) )
    # set_value()
# Label


def information( message ):
    """Show info message to user."""

    d = gtk.MessageDialog( type=gtk.MESSAGE_INFO,
                           message_format=message,
                           buttons=gtk.BUTTONS_CLOSE )
    d.run()
    d.destroy()
    return
# information()
info = information


def warning( message ):
    """Show warning message to user."""

    d = gtk.MessageDialog( type=gtk.MESSAGE_WARNING,
                           message_format=message,
                           buttons=gtk.BUTTONS_CLOSE )
    d.run()
    d.destroy()
    return
# warning()
warn = warning


def error( message ):
    """Show error message to user."""

    d = gtk.MessageDialog( type=gtk.MESSAGE_ERROR,
                           message_format=message,
                           buttons=gtk.BUTTONS_CLOSE )
    d.run()
    d.destroy()
    return
# error()
err = error


def yesno( message, yesdefault=False ):
    """Show yes/no message to user.

    @param yesdefault: if yes should be the default action.
    """

    d = gtk.MessageDialog( type=gtk.MESSAGE_QUESTION,
                           message_format=message,
                           buttons=gtk.BUTTONS_YES_NO )
    if yesdefault:
        d.set_default_response( gtk.RESPONSE_YES )
    else:
        d.set_default_response( gtk.RESPONSE_NO )

    r = d.run()
    d.destroy()

    if r == gtk.RESPONSE_YES:
        return True
    elif r == gtk.RESPONSE_NO:
        return False
    else:
        return yesdefault
# yesno()
    


def confirm( message, okdefault=False ):
    """Show confirm message to user.

    @param okdefault: if ok should be the default action.
    """

    d = gtk.MessageDialog( type=gtk.MESSAGE_QUESTION,
                           message_format=message,
                           buttons=gtk.BUTTONS_OK_CANCEL )
    if okdefault:
        d.set_default_response( gtk.RESPONSE_OK )
    else:
        d.set_default_response( gtk.RESPONSE_CANCEL )

    r = d.run()
    d.destroy()

    if r == gtk.RESPONSE_OK:
        return True
    elif r == gtk.RESPONSE_CANCEL:
        return False
    else:
        return okdefault
# confirm()



def run():
    """Enter the event loop"""
    try:
        gtk.main()
    except KeyboardInterrupt:
        raise SystemExit( "User quit using Control-C" )
# run()

def quit():
    """Quit the event loop"""
    gtk.main_quit()
# quit()


def get_app_by_id( app_id ):
    """Given an App unique identifier, return the reference to it."""
    if app_id is None:
        try:
            return _apps.values()[ 0 ]
        except IndexError, e:
            raise ValueError( "No application defined!" )
    elif isinstance( app_id, ( str, unicode ) ):
        try:
            return _apps[ app_id ]
        except KeyError, e:
            raise ValueError( "Application id \"%s\" doesn't exists!" % \
                              app_id )
    elif isinstance( app_id, App ):
        return app_id
    else:
        raise ValueError( "app_id must be string or App instance!" )
# get_app_by_id()


def get_widget_by_id( widget_id, app_id=None ):
    """Given an Widget unique identifier, return the reference to it.

    If app_id is not provided, will use the first App found.

    @attention: Try to always provide app_id since it may lead to problems if
    your program have more than one App.
    """
    app = get_app_by_id( app_id )

    if app:
        w = app.get_widget_by_id( widget_id )
        if not w:
            raise ValueError( "Widget id \"%s\" doesn't exists!" % widget_id )
        else:
            return w
# get_widget_by_id()


def get_value( widget_id, app_id=None ):
    """Convenience function to get widget and call its get_value() method."""
    try:
        wid = get_widget_by_id( widget_id, app_id )
        return wid.get_value()
    except ValueError, e:
        raise ValueError( e )
# get_value()


def set_value( widget_id, value, app_id=None ):
    """Convenience function to get widget and call its set_value() method."""
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_value( value )
    except ValueError, e:
        raise ValueError( e )
# set_value()


def show( widget_id, app_id=None ):
    """Convenience function to get widget and call its show() method."""
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.show()
    except ValueError, e:
        raise ValueError( e )
# show()


def hide( widget_id, app_id=None ):
    """Convenience function to get widget and call its hide() method."""
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.hide()
    except ValueError, e:
        raise ValueError( e )
# hide()


def set_active( widget_id, active=True, app_id=None ):
    """Convenience function to get widget and call its set_active() method."""
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_active( active )
    except ValueError, e:
        raise ValueError( e )
# set_active()


def set_inactive( widget_id, app_id=None ):
    """
    Convenience function to get widget and call its set_inactive() method.
    """
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_inactive()
    except ValueError, e:
        raise ValueError( e )
# set_inactive()


def close( app_id=None ):
    """Convenience function to get app and call its close() method."""
    try:
        app = get_app_by_id( app_id )
        app.close()
    except ValueError, e:
        raise ValueError( e )
# close()
