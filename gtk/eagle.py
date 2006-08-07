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
__url__ = "http://www.gustavobarbieri.com.br/eagle/"
__version__ = "0.7"
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
    "Group", "Tabs", "Table",
    "HSeparator", "VSeparator",
    "Label",
    "Canvas", "Image",
    "information", "info", "error", "err", "warning", "warn",
    "yesno", "confirm",
    "AboutDialog", "HelpDialog", "FileChooser",
    "RichText",
    "ExpandPolicy",
    ]

import os
import sys
import gc
import cPickle as pickle
import htmllib
import formatter
import weakref

try:
    import pygtk
    pygtk.require( "2.0" )
    import gtk
    import pango
    import gobject
except ImportError, e:
    sys.stderr.writelines(
        ( "Missing module: ", str( e ), "\n",
          "This module is part of pygtk (http://pygtk.org).\n",
          ) )
    sys.exit( -1 )

required_gtk = ( 2, 6, 0 )
m = gtk.check_version( *required_gtk )
if m:
    sys.stderr.writelines(
        ( "Error checking GTK version: %s\n"
          "This system requires pygtk >= %s, you have %s installed.\n" )
        % ( m,
            ".".join( [ str( v ) for v in required_gtk ] ),
            ".".join( [ str( v ) for v in gtk.pygtk_version ] )
            ) )
    sys.exit( -1 )


if not sys.platform.startswith( "win" ):
    gtk.gdk.threads_init() # enable threads

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


class _ExpandRule( object ):
    __slots__ = ( "fill", "expand" )
    def __init__( self, expand=False, fill=True ):
        self.expand = expand
        self.fill = fill
    # __init__()


    def __get_gtk_resize_policy__( self ):
        p = 0
        if self.expand:
            p |= gtk.EXPAND
        if self.fill:
            p |= gtk.FILL
        return p
    # __get_gtk_resize_policy__()


    def __str__( self ):
        return "ExpandRule( expand=%s, fill=%s )" % \
               ( self.expand, self.fill )
    # __str__()
    __repr__ = __str__
# _ExpandRule

class ExpandPolicy( object ):
    class Policy( object ):
        Rule = _ExpandRule
        __slots__ = ( "horizontal", "vertical" )

        def __init__( self, **kargs ):
            def conv_arg( arg ):
                if isinstance( arg, _ExpandRule ):
                    return arg
                elif isinstance( arg, ( tuple, list ) ):
                    return  _ExpandRule( *arg )
                elif isinstance( arg, dict ):
                    return _ExpandRule( **arg )
            # conv_arg()

            h = kargs.get( "horizontal", None )
            if h is not None:
                self.horizontal = conv_arg( h )
            else:
                self.horizontal = _ExpandRule()

            v = kargs.get( "vertical", None )
            if v is not None:
                self.vertical = conv_arg( v )
            else:
                self.vertical = _ExpandRule()
        # __init__()


        def __str__( self ):
            return "%s( horizontal=%s, vertical=%s )" % \
                   ( self.__class__.__name__, self.horizontal, self.vertical )
        # __str__()
        __repr__ = __str__
    # Policy


    class All( Policy ):
        horizontal = _ExpandRule( expand=True, fill=True )
        vertical = _ExpandRule( expand=True, fill=True )
        def __init__( self ): pass
    # All


    class Nothing( Policy ):
        horizontal = _ExpandRule( expand=False, fill=False )
        vertical =  _ExpandRule( expand=False, fill=False )
        def __init__( self ): pass
    # Nothing


    class Horizontal( Policy ):
        horizontal = _ExpandRule( expand=True, fill=True )
        vertical = _ExpandRule( expand=False, fill=True )
        def __init__( self ): pass
    # Horizontal


    class Vertical( Policy ):
        horizontal = _ExpandRule( expand=False, fill=True )
        vertical = _ExpandRule( expand=True, fill=True )
        def __init__( self ): pass
    # Vertical


    class FillHorizontal( Policy ):
        horizontal = _ExpandRule( expand=False, fill=True )
        vertical = _ExpandRule( expand=False, fill=False )
        def __init__( self ): pass
    # FillHorizontal


    class FillVertical( Policy ):
        horizontal = _ExpandRule( expand=False, fill=False )
        vertical = _ExpandRule( expand=False, fill=True )
        def __init__( self ): pass
    # FillVertical


    class Fill( Policy ):
        horizontal = _ExpandRule( expand=False, fill=True )
        vertical = _ExpandRule( expand=False, fill=True )
        def __init__( self ): pass
    # Fill
# ExpandPolicy



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

        if self.horizontal:
            orientation = _EGWidget.ORIENTATION_HORIZONTAL
        else:
            orientation = _EGWidget.ORIENTATION_VERTICAL

        for idx, c in enumerate( self.children ):
            c.__configure_orientation__( orientation )
            w = c.__get_widgets__()
            policy = c.expand_policy

            if len( w ) == 1:
                # use last one, in case of LabelEntry without label
                if isinstance( policy, ( tuple, list ) ):
                    policy = policy[ -1 ]

                xrm = policy.horizontal.__get_gtk_resize_policy__()
                yrm = policy.vertical.__get_gtk_resize_policy__()

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
                if not isinstance( policy, ( tuple, list ) ):
                    policy = ( policy, policy )

                xrm = ( policy[ 0 ].horizontal.__get_gtk_resize_policy__(),
                        policy[ 1 ].horizontal.__get_gtk_resize_policy__() )
                yrm = ( policy[ 0 ].vertical.__get_gtk_resize_policy__(),
                        policy[ 1 ].vertical.__get_gtk_resize_policy__() )

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
                             xoptions=xrm[ 0 ],
                             yoptions=yrm[ 0 ],
                             xpadding=self.padding,
                             ypadding=self.padding )
                self.attach( w[ 1 ], col2, col3, row2, row3,
                             xoptions=xrm[ 1 ],
                             yoptions=yrm[ 1 ],
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
    _id2obj_ = weakref.WeakValueDictionary()

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
        id = kargs.get( "id" ) or self.__get_id__()
        _EGObject.__init__( self, id )

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

        Image._id2obj_[ self.id ] = self
    # __init__()


    def __get_gtk_pixbuf__( self ):
        return self._img
    # __get_gtk_pixbuf__()


    def __get_by_id__( klass, id ):
        return klass._id2obj_[ id ]
    # __get_by_id__()
    __get_by_id__ = classmethod( __get_by_id__ )


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

    def __init__( self, id, app=None, expand_policy=None ):
        _EGObject.__init__( self, id )
        if app is not None:
            self.app = app
        self._widgets = tuple()
        self.expand_policy = expand_policy or ExpandPolicy.All()
    # __init__()


    def __get_widgets__( self ):
        """Return a list of B{internal} widgets this Eagle widget contains.

        @warning: never use it directly in Eagle applications!
        """
        return self._widgets
    # __get_widgets__()


    ORIENTATION_VERTICAL = 0
    ORIENTATION_HORIZONTAL = 1
    def __configure_orientation__( self, setting ):
        pass
    # __configure_orientation__()



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

    def __init__( self, id, persistent, app=None, expand_policy=None ):
        _EGWidget.__init__( self, id, expand_policy=expand_policy )
        if app is not None:
            self.app = app
        self.persistent = persistent
        self._widgets = tuple()
    # __init__()


    def get_value( self ):
        """Get data from this widget."""
        raise NotImplementedError( "%s doesn't implement get_value()" %
                                   self.__class__.__name__ )
    # get_value()

    def set_value( self, value ):
        """Set data to this widget."""
        raise NotImplementedError( "%s doesn't implement set_value()" %
                                   self.__class__.__name__ )
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

        self._text = RichText( id="About-%s" % self.app.id )
        self._diag.vbox.pack_start( self._text._widgets[ 0 ], True, True )

        self.__setup_text__()
    # __setup_gui__()


    def __setup_text__( self ):
        self._text.append( "<h1>%s</h1>" % self.title )

        if self.version:
            v = ".".join( self.version )
            self._text.append( "<i>%s</i>" % v )

        self._text.append( "<hr />" )

        if self.description:
            self._text.append( "<h2>Description</h2>" )
            for l in self.description:
                self._text.append( "<p>%s</p>" % l )

        if self.license:
            self._text.append( "<h2>License</h2><p>" )
            self._text.append( ", ".join( self.license ) )
            self._text.append( "</p>" )

        if self.author:
            if len( self.author ) == 1:
                self._text.append( "<h2>Author</h2>" )
            else:
                self._text.append( "<h2>Authors</h2>" )

            self._text.append( "<ul>" )
            for a in self.author:
                self._text.append( "<li>%s</li>" % a )
            self._text.append( "</ul>" )

        if self.help:
            self._text.append( "<h2>Help</h2>" )
            for l in self.help:
                self._text.append( "<p>%s</p>" % l )

        if self.copyright:
            self._text.append( "<h2>Copyright</h2>" )
            for l in self.copyright:
                self._text.append( "<p>%s</p>" % l )
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

        self._text = RichText( id="About-%s" % self.app.id )
        self._diag.vbox.pack_start( self._text._widgets[ 0 ], True, True )

        self.__setup_text__()
    # __setup_gui__()


    def __setup_text__( self ):
        self._text.append( "<h1>%s</h1>" % self.title )
        self._text.append( "<h2>Help</h2>" )
        for l in self.help:
            self._text.append( "<p>%s</p>" % l )
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
        progname = os.path.split( sys.argv[ 0 ] )[ -1 ]
        filename = "%s-%s-%s.tb" % ( progname,
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
        sys.stderr.write( "Traceback saved to '%s'.\n" % filename )
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
            filename = filename.replace( os.getcwd(), '' )[ 1 : ]

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

    def __init__( self, id, persistent, label="", expand_policy=None ):
        """
        @param expand_policy: one or two ExpandPolicy elements. If just
               one is provided, it will be used for both inner elements.
               If two are provided, first will be used for label and
               second for entry.
        """
        if expand_policy is None:
            expand_policy = ( ExpandPolicy.Fill(),
                              ExpandPolicy.Horizontal() )
        elif not isinstance( expand_policy, ( list, tuple ) ):
            expand_policy = ( expand_policy, expand_policy )

        _EGDataWidget.__init__( self, id, persistent,
                                expand_policy=expand_policy )
        self.__label = label
        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        if self.__label is not None:
            self._label = gtk.Label( self.__label )
            self._label.set_mnemonic_widget( self._entry )
            self._widgets = ( self._label, self._entry )
        else:
            self._widgets = ( self._entry, )
    # __setup_gui__()


    def __configure_orientation__( self, setting ):
        if self.label:
            if   setting == self.ORIENTATION_VERTICAL:
                self._label.set_justify( gtk.JUSTIFY_RIGHT )
                self._label.set_alignment( xalign=1.0, yalign=0.5 )
            elif setting == self.ORIENTATION_HORIZONTAL:
                self._label.set_justify( gtk.JUSTIFY_LEFT )
                self._label.set_alignment( xalign=0.0, yalign=1.0 )
    # __configure_orientation__()


    def get_value( self ):
        return self._entry.get_value()
    # get_value()


    def set_value( self, value ):
        self._entry.set_value( value )
    # set_value()


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        self._label.set_text( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )


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
    statusbar = _gen_ro_property( "statusbar" )
    _widgets = _gen_ro_property( "_widgets" )

    def __init__( self, title, id=None,
                  center=None, left=None, right=None, top=None, bottom=None,
                  preferences=None, window_size=( 800, 600 ),
                  quit_callback=None, data_changed_callback=None,
                  author=None, description=None, help=None, version=None,
                  license=None, copyright=None,
                  statusbar=False ):
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
        @param window_size: tuple of ( width, height ) or None to use the
               minimum size.
        @param statusbar: if C{True}, an statusbar will be available and
               usable with L{status_message} method.
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
               parameter the reference to App. If return value is False,
               it will abort closing the window.
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
        self.window_size = window_size
        self.author = _str_tuple( author )
        self.description = _str_tuple( description )
        self.help = _str_tuple( help )
        self.version = _str_tuple( version )
        self.license = _str_tuple( license )
        self.copyright = _str_tuple( copyright )
        self.statusbar = statusbar
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
        if w is None:
            raise ValueError( "Could not find any widget with id=%r" % name )
        elif isinstance( w, _EGDataWidget ):
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
        if self.window_size:
            self._win.set_default_size( *self.window_size )

        self._top_layout = gtk.VBox( False )
        self._win.add( self._top_layout )

        self._vbox = gtk.VBox( False, self.spacing )
        self._hbox = gtk.HBox( False, self.spacing )
        self._hbox.set_border_width( self.border_width )
        self._top_layout.pack_start( self._vbox, expand=True, fill=True )

        self.__setup_gui_left__()
        self.__setup_gui_right__()
        self.__setup_gui_center__()
        self.__setup_gui_top__()
        self.__setup_gui_bottom__()
        self.__setup_gui_preferences__()

        has_top = bool( self._top.__get_widgets__() )
        has_bottom = bool( self._bottom.__get_widgets__() )
        has_left = bool( self._left.__get_widgets__() )
        has_right = bool( self._right.__get_widgets__() )
        has_center = bool( self._center.__get_widgets__() )

        expand_top = False
        expand_bottom = False
        expand_left = False
        expand_right = False
        expand_center = has_center
        has_hl = has_left or has_center or has_right

        # Left and Right just expand if there is no center
        if has_left and not has_center:
            expand_left = True
        if has_right and not has_center:
            expand_right = True

        # Top and Bottom just expand if there is no center
        if has_top and not has_hl:
            expand_top = True
        if has_bottom and not has_hl:
            expand_bottom = True

        # Create Horizontal layout with ( Left | Center | Right )
        if has_hl:
            if has_left:
                self._hbox.pack_start( self._left, expand_left, True )
                if has_center or has_right:
                    self._hbox.pack_start( gtk.VSeparator(), False, True )

            if has_center:
                self._hbox.pack_start( self._center, expand_center, True )
                if has_right:
                    self._hbox.pack_start( gtk.VSeparator(), False, True )

            if has_right:
                self._hbox.pack_start( self._right, expand_right, True )

        # Create Vertical layout with ( TOP | HL | Bottom )
        # where HL is Horizontal layout created before
        if has_top:
            self._vbox.pack_start( self._top, expand_top, True )
            if has_hl or has_bottom:
                self._vbox.pack_start( gtk.HSeparator(), False, True )

        if has_hl:
            self._vbox.pack_start( self._hbox, True, True )
            if has_bottom:
                self._vbox.pack_start( gtk.HSeparator(), False, True )

        if has_bottom:
            self._vbox.pack_start( self._bottom, expand_bottom, True )


        if self.statusbar:
            self._statusbar = gtk.Statusbar()
            self._statusbar_ctx = self._statusbar.get_context_id( self.title )
            self._statusbar.set_has_resize_grip( True )
            self._top_layout.pack_end( self._statusbar,
                                       expand=False, fill=True )

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


    def __do_close__( self ):
        self.save()

        for c in self.quit_callback:
            if not c( self ):
                return False

        del _apps[ self.id ]
        if not _apps:
            gtk.main_quit()

        return True
    # __do_close__()


    def __delete_event__( self, *args ):
        if self.__do_close__():
            return False
        else:
            return True
    # __delete_event__()


    def __persistence_filename__( self ):
        fname = "%s.save_data" % self.id

        if sys.platform.startswith( "win" ):
            appdata = os.environ.get( "APPDATA", "C:" )
            binname = os.path.realpath( sys.argv[ 0 ] ).replace( ":", "" )
            d = os.path.join( appdata, "Eagle", binname )
        else:
            home = os.environ.get( "HOME", "." )
            binname = os.path.realpath( sys.argv[ 0 ] )[ 1 : ]
            d = os.path.join( home, ".eagle", binname )

        if not os.path.exists( d ):
            os.makedirs( d )

        return os.path.join( d, fname )
    # __persistence_filename__()


    def save( self ):
        """Save data from widgets to file.

        Probably you will not need to call this directly.
        """
        d = {}
        for id, w in self._widgets.iteritems():
            if isinstance( w, _EGDataWidget ) and w.persistent:
                d[ id ] = w.get_value()

        if d:
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
        if self.__do_close__():
            self._win.destroy()
    # close()


    def status_message( self, message ):
        """Display a message in status bar and retrieve its identifier for
        later removal.

        @see: L{remove_status_message}
        @note: this only active if statusbar=True
        """
        if self.statusbar:
            return self._statusbar.push( self._statusbar_ctx, message )
        else:
            raise ValueError( "App '%s' doesn't use statusbar!" % self.id )
    # status_message()


    def remove_status_message( self, message_id ):
        """Remove a previously displayed message.

        @see: L{status_message}
        @note: this only active if statusbar=True
        """
        if self.statusbar:
            self._statusbar.remove( self._statusbar_ctx, message_id )
        else:
            raise ValueError( "App '%s' doesn't use statusbar!" % self.id )
    # remove_status_message()


    def timeout_add( self, interval, callback ):
        """Register a function to be called after a given timeout/interval.

        @param interval: milliseconds between calls.
        @param callback: function to call back. This function gets as
               argument the app reference and must return C{True} to
               keep running, if C{False} is returned, it will not be
               called anymore.
        @return: id number to be used in L{remove_event_source}
        """
        def wrap( *args ):
            return callback( self )
        # wrap()
        return gobject.timeout_add( interval, wrap )
    # timeout_add()


    def idle_add( self, callback ):
        """Register a function to be called when system is idle.

        System is idle if there is no other event pending.

        @param callback: function to call back. This function gets as
               argument the app reference and must return C{True} to
               keep running, if C{False} is returned, it will not be
               called anymore.
        @return: id number to be used in L{remove_event_source}
        """
        def wrap( *args ):
            return callback( self )
        # wrap()
        return gobject.idle_add( wrap )
    # idle_add()



    def io_watch( self, file, callback,
                  on_in=False, on_out=False, on_urgent=False, on_error=False,
                  on_hungup=False ):
        """Register a function to be called after an Input/Output event.

        @param file: any file object or file descriptor (integer).
        @param callback: function to be called back, parameters will be the
               application that generated the event, the file that triggered
               it and on_in, on_out, on_urgent, on_error or on_hungup,
               being True those that triggered the event.
               The function must return C{True} to be called back again,
               otherwise it is automatically removed.
        @param on_in: there is data to read.
        @param on_out: data can be written without blocking.
        @param on_urgent: there is urgent data to read.
        @param on_error: error condition.
        @param on_hungup: hung up (the connection has been broken, usually for
               pipes and sockets).
        @return: id number to be used in L{remove_event_source}
        """
        def wrap( source, cb_condition ):
            on_in     = bool( cb_condition & gobject.IO_IN )
            on_out    = bool( cb_condition & gobject.IO_OUT )
            on_urgent = bool( cb_condition & gobject.IO_PRI )
            on_error  = bool( cb_condition & gobject.IO_ERR )
            on_hungup = bool( cb_condition & gobject.IO_HUP )
            return callback( self, source, on_in=on_in,
                             on_out=on_out, on_urgent=on_urgent,
                             on_error=on_error, on_hungup=on_hungup )
        # wrap()

        condition = 0
        if on_in:
            condition |= gobject.IO_IN
        if on_out:
            condition |= gobject.IO_OUT
        if on_urgent:
            condition |= gobject.IO_PRI
        if on_error:
            condition |= gobject.IO_ERR
        if on_hungup:
            condition |= gobject.IO_HUP
        return gobject.io_add_watch( file, condition, wrap )
    # io_watch()


    def remove_event_source( self, event_id ):
        """Remove an event generator like those created by L{timeout_add},
        L{idle_add} or L{io_watch}.

        @param event_id: value returned from L{timeout_add},
        L{idle_add} or L{io_watch}.

        @return: C{True} if it was removed.
        """
        return gobject.source_remove( event_id )
    # remove_event_source()
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

    MOUSE_BUTTON_1         = 1
    MOUSE_BUTTON_2         = 2
    MOUSE_BUTTON_3         = 4
    MOUSE_BUTTON_4         = 8
    MOUSE_BUTTON_5         = 16

    label = _gen_ro_property( "label" )

    def __init__( self, id, width, height, label="", bgcolor=None,
                  scrollbars=True, callback=None, expand_policy=None ):
        """Canvas Constructor.

        @param id: unique identifier.
        @param width: width of the drawing area in pixels, widget can be
               larger or smaller because and will use scrollbars if need.
        @param height: height of the drawing area in pixels, widget can be
               larger or smaller because and will use scrollbars if need.
        @param label: label to display in the widget frame around the
               drawing area. If None, no label or frame will be shown.
        @param bgcolor: color to paint background.
        @param scrollbars: whenever to use scrollbars and make canvas
               fit small places.
        @param callback: function (or list of functions) to call when
               mouse state changed in the drawing area. Function will get
               as parameters:
                - App reference
                - Canvas reference
                - Button state (or'ed MOUSE_BUTTON_*)
                - horizontal positon (x)
                - vertical positon (y)
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.

        @todo: honor the alpha value while drawing colors.
        """
        _EGWidget.__init__( self, id, expand_policy=expand_policy )
        self.__label = label
        self.width = width
        self.height = height
        self.scrollbars = scrollbars

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
        self._sw = gtk.ScrolledWindow()
        self._area = gtk.DrawingArea()

        self._sw.set_border_width( self.padding )

        if self.label is not None:
            self._frame = gtk.Frame( self.label )
            self._frame.add( self._sw )
            self._frame.set_shadow_type( gtk.SHADOW_OUT )
            root = self._frame
        else:
            root = self._sw

        self._area.set_size_request( width, height )
        self._sw.add_with_viewport( self._area )
        if self.scrollbars:
            policy = gtk.POLICY_AUTOMATIC
            border = gtk.SHADOW_IN
        else:
            policy = gtk.POLICY_NEVER
            border = gtk.SHADOW_NONE

        self._sw.set_policy( hscrollbar_policy=policy,
                             vscrollbar_policy=policy )
        self._sw.child.set_shadow_type( border )
        self._sw.show_all()

        self._widgets = ( root, )
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


        def get_buttons( state ):
            buttons = 0
            if state & gtk.gdk.BUTTON1_MASK:
                buttons |= self.MOUSE_BUTTON_1
            if state & gtk.gdk.BUTTON2_MASK:
                buttons |= self.MOUSE_BUTTON_2
            if state & gtk.gdk.BUTTON3_MASK:
                buttons |= self.MOUSE_BUTTON_3
            if state & gtk.gdk.BUTTON4_MASK:
                buttons |= self.MOUSE_BUTTON_4
            if state & gtk.gdk.BUTTON5_MASK:
                buttons |= self.MOUSE_BUTTON_5
            return buttons
        # get_buttons()

        buttons_map = {
            1: self.MOUSE_BUTTON_1,
            2: self.MOUSE_BUTTON_2,
            3: self.MOUSE_BUTTON_3,
            4: self.MOUSE_BUTTON_4,
            5: self.MOUSE_BUTTON_5,
            }

        def button_press_event( widget, event ):
            if self._pixmap != None:
                btns = get_buttons( event.state )
                btns |= buttons_map[ event.button ]

                x = int( event.x )
                y = int( event.y )

                for c in self._callback:
                    c( self.app, self, btns, x, y )
            return True
        # button_press_event()
        if self._callback:
            self._area.connect( "button_press_event", button_press_event )


        def button_release_event( widget, event ):
            if self._pixmap != None:
                btns = get_buttons( event.state )
                btns &= ~buttons_map[ event.button ]

                x = int( event.x )
                y = int( event.y )

                for c in self._callback:
                    c( self.app, self, btns, x, y )
            return True
        # button_press_event()
        if self._callback:
            self._area.connect( "button_release_event", button_release_event )


        def motion_notify_event( widget, event ):
            if self._pixmap is None:
                return True

            if event.is_hint:
                x, y, state = event.window.get_pointer()
            else:
                x = event.x
                y = event.y
                state = event.state


            btns = get_buttons( state )
            x = int( x )
            y = int( y )

            if btns:
                for c in self._callback:
                    c( self.app, self, btns, x, y )

            return True
        # motion_notify_event()
        if self._callback:
            self._area.connect( "motion_notify_event", motion_notify_event )


        # Enable events
        self._area.set_events( gtk.gdk.EXPOSURE_MASK |
                               gtk.gdk.LEAVE_NOTIFY_MASK |
                               gtk.gdk.BUTTON_PRESS_MASK |
                               gtk.gdk.BUTTON_RELEASE_MASK |
                               gtk.gdk.POINTER_MOTION_MASK |
                               gtk.gdk.POINTER_MOTION_HINT_MASK )
    # __setup_connections__()



    def __color_from__( color ):
        """Convert from color to internal representation.

        Gets a string, integer or tuple/list arguments and converts into
        internal color representation.
        """
        a = 255

        if isinstance( color, str ):
            try:
                c = gtk.gdk.color_parse( color )
                r = int( c.red   / 65535.0 * 255 )
                g = int( c.green / 65535.0 * 255 )
                b = int( c.blue  / 65535.0 * 255 )
            except ValueError, e:
                raise ValueError( "%s. color=%r" % ( e, color ) )
        elif isinstance( color, gtk.gdk.Color ):
            r = int( color.red   / 65535.0 * 255 )
            g = int( color.green / 65535.0 * 255 )
            b = int( color.blue  / 65535.0 * 255 )
        elif isinstance( color, int ):
            r = ( color >> 16 ) & 0xff
            g = ( color >>  8 ) & 0xff
            b = ( color & 0xff )
        elif isinstance( color, ( tuple, list ) ):
            if len( color) == 3:
                r, g, b = color
            else:
                a, r, g, b = color

        return a, r, g, b
    # __color_from__()
    __color_from__ = staticmethod( __color_from__ )


    def __to_gtk_color__( color ):
        r = int( color[ 1 ] / 255.0 * 65535 )
        g = int( color[ 2 ] / 255.0 * 65535 )
        b = int( color[ 3 ] / 255.0 * 65535 )
        return gtk.gdk.Color( r, g, b )
    # __to_gtk_color__()
    __to_gtk_color__ = staticmethod( __to_gtk_color__ )


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
            gc.set_rgb_fg_color( self.__to_gtk_color__( fgcolor ) )
        if bgcolor is not None:
            gc.set_rgb_bg_color( self.__to_gtk_color__( bgcolor ) )
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
                   font_family=None,
                   width=None, wrap_word=False,
                   alignment=LEFT, justify=True ):
        """Draw text on canvas.

        By default text is draw with current font and colors at top canvas
        corner.

        You may limit width providing a value and choose if it should wrap
        at words (wrap_word=True) or characters (wrap_word=False).


        Colors can be specified with fgcolor an bgcolor. If not provided, the
        system foreground color is used and no background color is used.

        Font name, family, size and options may be specified using
        font_name, font_family, font_size and font_options, respectively.
        Try to avoid using system specific font fames, use those provided
        by FONT_NAME_*.

        Font options is OR'ed values from FONT_OPTIONS_*.

        Font name is a string that have all the information, like
        "sans bold 12". This is returned by L{Font}.

        Text alignment is one of LEFT, RIGHT or CENTER.
        """
        if fgcolor is not None:
            fgcolor = self.__to_gtk_color__( self.__color_from__( fgcolor ) )
        if bgcolor is not None:
            bgcolor = self.__to_gtk_color__( self.__color_from__( bgcolor ) )

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

        if font_name or font_size or font_options or font_family:
            if font_name:
                fd = pango.FontDescription( font_name )
            else:
                fd = layout.get_context().get_font_description()

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

        size2 = size * 2

        w, h = abs( x1 - x0 ) + size2, abs( y1 - y0 ) + size2
        x, y = max( min( x0, x1 ) - size, 0 ), max( min( y0, y1 ) - size, 0 )
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


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        self._frame.set_label( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )


    def __str__( self ):
        return "%s( id=%r, width=%r, height=%r, label=%r )" % \
               ( self.__class__.__name__, self.id, self.width, self.height,
                 self.label )
    # __str__()
    __repr__ = __str__
# Canvas


class _MultiLineEntry( gtk.ScrolledWindow ):
    def __init__( self ):
        gtk.ScrolledWindow.__init__( self )
        self.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                         vscrollbar_policy=gtk.POLICY_AUTOMATIC )
        self.set_shadow_type( gtk.SHADOW_IN )

        self.textview = gtk.TextView()
        self.add( self.textview )

        self.textview.set_editable( True )
        self.textview.set_cursor_visible( True )
        self.textview.set_left_margin( 2 )
        self.textview.set_right_margin( 2 )
        self.textview.get_buffer().connect( "changed", self.__emit_changed__ )
    # __init__()


    def __emit_changed__( self, *args ):
        self.emit( "changed" )
    # __emit_changed__


    def set_text( self, value ):
        self.textview.get_buffer().set_text( value )
    # set_text()


    def get_text( self ):
        b = self.textview.get_buffer()
        return b.get_text( b.get_start_iter(), b.get_end_iter() )
    # get_text()


    def set_editable( self, setting ):
        self.textview.set_editable( setting )
    # set_editable()
# _MultiLineEntry
gobject.signal_new( "changed",
                    _MultiLineEntry,
                    gobject.SIGNAL_RUN_LAST,
                    gobject.TYPE_NONE,
                    tuple() )


class Entry( _EGWidLabelEntry ):
    """Text entry.

    The simplest user input component. Its contents are free-form and not
    filtered/masked.
    """
    value = _gen_ro_property( "value" )
    callback = _gen_ro_property( "callback" )
    multiline = _gen_ro_property( "multiline" )


    def __init__( self, id, label="", value="", callback=None,
                  editable=True, persistent=False, multiline=False,
                  expand_policy=None ):
        """Entry constructor.

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param editable: if this field is editable by user.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        @param multiline: if this entry can be multi-line.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.value = value
        self.callback = _callback_tuple( callback )
        self.multiline = bool( multiline )
        self._editable = editable

        if expand_policy is None:
            if self.multiline:
                p = ExpandPolicy.All()
            else:
                p = ExpandPolicy.Horizontal()

            expand_policy = ( ExpandPolicy.Fill(), p )

        _EGWidLabelEntry.__init__( self, id, persistent, label,
                                   expand_policy=expand_policy )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        if self.multiline:
            self._entry = _MultiLineEntry()
        else:
            self._entry = gtk.Entry()

        self._entry.set_name( self.id )
        self._entry.set_text( self.value )
        self.set_editable( self._editable )

        _EGWidLabelEntry.__setup_gui__( self )
    # __setup_gui__()


    def __configure_orientation__( self, setting ):
        super( Entry, self ).__configure_orientation__( setting )
        if self.multiline and self.label and \
               setting == self.ORIENTATION_VERTICAL:
            self._label.set_alignment( xalign=1.0, yalign=0 )
    # __configure_orientation__()


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


    def set_editable( self, value ):
        self._editable = bool( value )
        self._entry.set_editable( self._editable )
    # set_editable()


    def get_editable( self ):
        return self._editable
    # set_editable()

    editable = property( get_editable, set_editable )
# Entry


class Password( Entry ):
    """Password entry.

    Like L{Entry}, but will show '*' instead of typed chars.
    """
    def __init__( self, id, label="", value="", callback=None,
                  persistent=False, expand_policy=None ):
        """Password constructor.

        @param id: unique identifier.
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
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        Entry.__init__( self, id, label, value, callback, persistent,
                        expand_policy=expand_policy )
        self._entry.set_visibility( False )
    # __init__()
# Password


class Spin( _EGWidLabelEntry ):
    """Spin button entry.

    Spin buttons are numeric user input that checks if value is inside
    a specified range. It also provides small buttons to help incrementing/
    decrementing value.
    """
    default_min = -1e60
    default_max =  1e60

    value = _gen_ro_property( "value" )
    min = _gen_ro_property( "min" )
    max = _gen_ro_property( "max" )
    step = _gen_ro_property( "step" )
    digits = _gen_ro_property( "digits" )

    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None, digits=3,
                  callback=None, persistent=False, expand_policy=None ):
        """Spin constructor.

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value. If None, L{default_min} will be used.
        @param max: maximum value. If None, L{default_max} will be used.
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
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.digits = digits
        self.callback = _callback_tuple( callback )

        _EGWidLabelEntry.__init__( self, id, persistent, label,
                                   expand_policy=expand_policy )

        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        k = {}

        if self.value is not None:
            k[ "value" ] = self.value

        if self.min is not None:
            k[ "lower" ] = self.min
        else:
            k[ "lower" ] = self.default_min

        if self.max is not None:
            k[ "upper" ] = self.max
        else:
            k[ "upper" ] = self.default_max

        if self.step is not None:
            k[ "step_incr" ] = self.step
            k[ "page_incr" ] = self.step * 2
        else:
            k[ "step_incr" ] = 1
            k[ "page_incr" ] = 2

        adj = gtk.Adjustment( **k )
        self._entry = gtk.SpinButton( adjustment=adj, digits=self.digits )
        self._entry.set_name( self.id )
        self._entry.set_numeric( True )
        self._entry.set_snap_to_ticks( False )

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
    default_min = -sys.maxint
    default_max =  sys.maxint

    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None,
                  callback=None, persistent=False, expand_policy=None ):
        """Integer Spin constructor.

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value. If None, L{default_min} will be used.
        @param max: maximum value. If None, L{default_max} will be used.
        @param step: step to use to decrement/increment using buttons.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
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
                       persistent, expand_policy=expand_policy )
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
    default_min = 0

    def __init__( self, id, label="",
                  value=None, min=0, max=None, step=None,
                  callback=None, persistent=False, expand_policy=None ):
        """Unsigned Integer Spin constructor.

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param value: initial content.
        @param min: minimum value, must be greater or equal zero.
        @param max: maximum value. If None, L{default_max} will be used.
        @param step: step to use to decrement/increment using buttons.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        if min < 0:
            raise ValueError( "UIntSpin cannot have min < 0!" )
        Spin.__init__( self, id, label, value, min, max, step, 0, callback,
                       persistent, expand_policy=expand_policy )
    # __init__()
# UIntSpin


class Color( _EGWidLabelEntry ):
    """Button to select colors.

    It show current/last selected color and may pop-up a new dialog to
    select a new one.
    """
    color = _gen_ro_property( "color" )
    use_alpha = _gen_ro_property( "use_alpha" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", color=0, use_alpha=False,
                  callback=None, persistent=False, expand_policy=None ):
        """Color selector constructor.

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param color: initial content. May be a triple with elements within
               the range 0-255, an string with color in HTML format or even
               a color present in X11's rgb.txt.
        @param use_alpha: if the alpha channel should be used, it will be
               the first value in the tuple representing the color.
        @param callback: function (or list of functions) that will
               be called when this widget have its data changed.
               Function will receive as parameters:
                - App reference
                - Widget reference
                - new value
        @param persistent: if this widget should save its data between
               sessions.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.color = self.color_from( color )
        self.use_alpha = use_alpha
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label,
                                   expand_policy=expand_policy )

        self.__setup_connections__()
    # __init__()


    def color_from( color ):
        a = 255
        if isinstance( color, str ):
            try:
                c = gtk.gdk.color_parse( color )
                r = int( c.red / 65535.0 * 255 )
                g = int( c.green / 65535.0 * 255 )
                b = int( c.blue / 65535.0 * 255 )
            except ValueError, e:
                raise ValueError( "%s. color=%r" % ( e, color ) )

        if isinstance( color, int ):
            r = ( color >> 16 ) & 0xff
            g = ( color >>  8 ) & 0xff
            b = ( color & 0xff )
        elif isinstance( color, ( tuple, list ) ):
            if len( color ) == 3:
                r, g, b = color
            else:
                a, r, g, b = color

        return a, r, g, b
    # color_from()
    color_from = staticmethod( color_from )


    def __setup_gui__( self ):
        r = int( self.color[ 1 ] / 255.0 * 65535 )
        g = int( self.color[ 2 ] / 255.0 * 65535 )
        b = int( self.color[ 3 ] / 255.0 * 65535 )

        c = gtk.gdk.Color( r, g, b )

        self._entry = gtk.ColorButton( c )
        self._entry.set_name( self.id )
        self._entry.set_use_alpha( self.use_alpha )
        if self.use_alpha:
            alpha = int( self.color[ 0 ] / 255.0 * 65535 )
            self._entry.set_alpha( alpha )
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
        """Return a tuple with ( alpha, red, green, blue )
          ( alpha, red, green, blue ) (use_alpha=True), each in 0-255 range.
        """
        c = self._entry.get_color()
        r = int( c.red   / 65535.0 * 255 )
        g = int( c.green / 65535.0 * 255 )
        b = int( c.blue  / 65535.0 * 255 )

        if self.use_alpha:
            a = int( self._entry.get_alpha() / 65535.0 * 255 )
            return ( a, r, g, b )
        else:
            return ( r, g, b )
    # get_value()


    def set_value( self, value ):
        """
        @param value: May be a triple with elements within
               the range 0-255, an string with color in HTML format or even
               a color present in X11's rgb.txt.
        """
        a, r, g, b = self.color_from( value )
        if self.use_alpha:
            self._entry.set_alpha( int( a / 255.0 * 65535.0 ) )

        r = int( r / 255.0 * 65535 )
        g = int( g / 255.0 * 65535 )
        b = int( b / 255.0 * 65535 )

        c = gtk.gdk.Color( r, g, b )
        self._entry.set_color( c )
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
                  persistent=False, expand_policy=None ):
        """Font selector constructor.

        @param id: unique identifier.
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
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.font = font
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label,
                                   expand_policy=expand_policy )

        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._entry = gtk.FontButton( self.font )
        self._entry.set_name( self.id )
        self._entry.set_show_style( True )
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
                  callback=None, persistent=False, expand_policy=None ):
        """Selection constructor.

        @param id: unique identifier.
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
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.options = options or []
        self.active  = active
        self.callback = _callback_tuple( callback )
        _EGWidLabelEntry.__init__( self, id, persistent, label,
                                   expand_policy=expand_policy )

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


    def append( self, value, set_active=False ):
        """Append new value to available options.

        @param value: string that is not already an option.

        @raise: ValueError: if value is already an option.
        """
        if value not in self.items():
            self._entry.append_text( value )
            if set_active:
                self.set_value( value )
        else:
            raise ValueError( "value already in selection" )
    # append()


    def prepend( self, value ):
        """Prepend new value to available options.

        @param value: string that is not already an option.

        @raise: ValueError: if value is already an option.
        """
        if value not in self.items():
            self._entry.prepend_text( value )
            if set_active:
                self.set_value( value )
        else:
            raise ValueError( "value already in selection" )
    # prepend()


    def insert( self, position, value ):
        """Insert new option at position.

        @param value: string that is not already an option.

        @raise: ValueError: if value is already an option.
        """
        if value not in self.items():
            self._entry.insert_text( position, value )
            if set_active:
                self.set_value( value )
        else:
            raise ValueError( "value already in selection" )
    # insert()


    def remove( self, value ):
        """Remove given value from available options.

        @param value: string that is an option.

        @raise ValueError: if value is not already an option.
        """
        for i, o in enumerate( self._entry.get_model() ):
            if o[ 0 ] == value:
                self._entry.remove_text( i )
                return

        raise ValueError( "value not in selection" )
    # remove()


    def items( self ):
        """Returns every item/option in this selection."""
        return [ str( x[ 0 ] ) for x in  self._entry.get_model() ]
    # items()
    options = items


    def __len__( self ):
        return len( self._entry.get_model() )
    # __len__()


    def __contains__( self, value ):
        return value in self.items()
    # __contains__()


    def __iadd__( self, value ):
        """Same as L{append}"""
        self.append( value )
    # __iadd__()


    def __isub__( self, value ):
        """Same as L{remove}"""
        self.remove( value )
    # __isub__()
# Selection


class Progress( _EGWidLabelEntry ):
    """Progress bar."""
    value = _gen_ro_property( "value" )

    def __init__( self, id, label="", value=0.0, expand_policy=None ):
        """Progress bar constructor.

        0 <= value <= 1.0

        @param id: unique identifier.
        @param label: what to show on a label on the left side of the widget.
        @param value: initial content ( 0.0 <= value <= 1.0 )
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.value = value
        _EGWidLabelEntry.__init__( self, id, False, label,
                                   expand_policy=expand_policy )
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
                  persistent=False, expand_policy=None ):
        """Check box constructor.

        @param id: unique identifier.
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
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        self.__label = label
        self.state = state
        self.callback = _callback_tuple( callback )

        if expand_policy is None:
            expand_policy = ExpandPolicy.Fill()

        _EGDataWidget.__init__( self, id, persistent,
                                expand_policy=expand_policy )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        self._wid = gtk.CheckButton( self.__label )
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


    def set_value( self, value ):
        return self._wid.set_active( bool( value ) )
    # set_value()


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        self._wid.set_label( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )
# CheckBox


class Group( _EGWidget ):
    """Group of various components.

    Group is a component that holds other components, always in a vertical
    layout.

    Group has a frame and may show a label.
    """
    children = _gen_ro_property( "children" )
    horizontal = _gen_ro_property( "horizontal" )

    BORDER_NONE = gtk.SHADOW_NONE
    BORDER_IN = gtk.SHADOW_IN
    BORDER_OUT = gtk.SHADOW_OUT
    BORDER_ETCHED_IN = gtk.SHADOW_ETCHED_IN
    BORDER_ETCHED_OUT = gtk.SHADOW_ETCHED_OUT

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


    def __init__( self, id, label="", children=None, horizontal=False,
                  border=BORDER_ETCHED_IN, expand_policy=None ):
        """Group constructor.

        @param id: unique identified.
        @param label: displayed at top-left.
        @param children: a list of eagle widgets that this group contains.
        @param horizontal: if widgets should be laid out horizontally.
        @param border: can be one of Group.BORDER_* values or None to
               disable border and label completely. Note that some themes
               may have different appearance for borders and some may not
               respect BORDER_NONE, so if you really want no border, use
               None to disable it. Note that Groups without borders cannot
               have one added later.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        if expand_policy is None:
            expand_policy = ExpandPolicy.Horizontal()

        _EGWidget.__init__( self, id, expand_policy=expand_policy )
        self.__label = label
        self.children = _obj_tuple( children )
        self.horizontal = bool( horizontal )
        self.__border = border

        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        self._contents = _Table( id=( "%s-contents" % self.id ),
                                 children=self.children,
                                 horizontal=self.horizontal )

        if self.border is not None:
            self._frame = gtk.Frame( self.__label )
            self._frame.set_name( self.id )
            self._frame.set_shadow_type( self.border )
            self._frame.add( self._contents )
            root = self._frame
        else:
            root = self._contents

        self._widgets = ( root, )
    # __setup_gui__()


    def __add_widgets_to_app__( self ):
        for w in self.children:
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        if self.border is not None:
            self._frame.set_label( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )


    def set_border( self, border ):
        if self.__border is None:
            raise ValueError( "You cannot change border of widget created "
                              "without one." )

        if border is not None:
            self._frame.set_shadow_type( border )
        else:
            raise ValueError( "You cannot remove widget border" )

        self.__border = border
    # set_border()


    def get_border( self ):
        return self.__border
    # get_border()

    border = property( get_border, set_border )
# Group


class Tabs( _EGWidget ):
    """Present widgets in Tabs.

    This is also known as TabControl, TabWidget, Notebook, etc in
    other toolkits.

    Tabs are composed from Pages (L{Tabs.Page}), which behave just
    like L{Group}s and hold a list of widgets.

    Pages can be accessed by their index number (integer) or label,
    using the dictionary syntax or L{Tabs.get_page()} method.
    """

    class Page( _EGWidget, AutoGenId ):
        """Page in Tabs component.

        Pages must have a name and optionally an id, otherwise one id
        will be automatically generated.

        It behaves just like L{Group} component.
        """
        spacing = 3

        children = _gen_ro_property( "children" )
        horizontal = _gen_ro_property( "horizontal" )
        parent = _gen_ro_property( "parent" )

        def __init__( self, id=None, label="", children=None,
                      horizontal=False ):
            """Tabs.Page constructor.

            @param id: may not be provided, it will be generated automatically.
            @param label: displayed as Page label.
            @param children: a list of eagle widgets that this page contains.
            @param horizontal: if widgets should be laid out horizontally.
            """
            _EGWidget.__init__( self, id or self.__get_id__() )
            self.__label = label or ""
            self.horizontal = bool( horizontal )
            self.children = _obj_tuple( children )
            self.parent = None
            self._gtk_label = gtk.Label( self.__label )

            self.__setup_gui__()
        # __init__()


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


        def __add_widgets_to_app__( self ):
            for w in self.children:
                self.app.__add_widget__( w )
        # __add_widgets_to_app__()


        def __setup_gui__( self ):
            self._wid = _Table( id=( "%s-contents" % self.id ),
                                children=self.children,
                                horizontal=self.horizontal )
            self._widgets = ( self._wid, )
        # __setup_gui__()


        def set_label( self, label ):
            if label is None:
                raise ValueError( "You cannot have 'None' labels for "
                                  "Tabs.Page!" )
            self.__label = str( label )
            self._gtk_label.set_text( self.__label )
        # set_label()


        def get_label( self ):
            return self.__label
        # get_label()

        label = property( get_label, set_label )


        def focus( self ):
            self.parent.__focus_page__( self )
        # focus()


        def set_active( self, value=True ):
            _EGWidget.set_active( self, value )
            self._gtk_label.set_sensitive( value )
        # set_active()
    # Page


    children = _gen_ro_property( "children" )


    def __init__( self, id, children=None, expand_policy=None ):
        """Tabs constructor.

        @param id: unique identified.
        @param children: an iterable with L{Tabs.Page}
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        if expand_policy is None:
            expand_policy = ExpandPolicy.All()

        _EGWidget.__init__( self, id, expand_policy=expand_policy )
        if not children:
            self.children = tuple()
        else:
            lst = []
            for i, widget in enumerate( children ):
                if isinstance( widget, Tabs.Page ):
                    lst.append( widget )
                else:
                    sys.stderr.write( ( "children #%d (%s) is not "
                                        "instance of Tabs.Page, but %s" ) %
                                      ( i, widget, type( widget ).__name__ ))
            self.children = tuple( lst )

        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        self._wid = gtk.Notebook()
        for w in self.children:
            w.parent = self
            self._wid.append_page( w._widgets[ 0 ], w._gtk_label )
        self._widgets = ( self._wid, )
    # __setup_gui__()


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


    def __add_widgets_to_app__( self ):
        for w in self.children:
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()


    def __focus_page__( self, page ):
        for index, p in enumerate( self.children ):
            if p == page:
                self._wid.set_current_page( index )
                return
        raise ValueError( "Page '%s' doesn't exist in this Tab." % ( page, ) )
    # __focus_page__()


    def focus_page( self, index_or_name_or_page ):
        """Make given page visible."""
        if not isinstance( index_or_name_or_page, Tabs.Page ):
            index_or_name = index_or_name_or_page
            page = self.get_page( index_or_name )
        else:
            page = index_or_name_or_page
        page.focus()
    # focus_page()


    def get_page( self, index_or_name ):
        """Get the Tabs.Page given its index or name.

        @raise KeyError if index_or_name doesn't exists.
        """
        if isinstance( index_or_name, basestring ):
            name = index_or_name
            for w in self.children:
                if w.label == name:
                    return w
            raise KeyError( "No page labeled '%s'" % name )
        else:
            index = index_or_name
            try:
                return self.children[ index ]
            except IndexError, e:
                raise KeyError( "No page numbered %s" % index )
    # get_page()


    def __getitem__( self, name ):
        """Same as L{Tabs.get_page()}.

        @raise KeyError see L{Tabs.get_page()}
        @see L{Tabs.get_page()}
        """
        return self.get_page( name )
    # __getitem__()


    def __setitem__( self, name, value ):
        """Set L{Tabs.Page.label} of a page get using 'name' for
        L{Tabs.get_page()}.

        @raise KeyError see L{Tabs.get_page()}
        @see L{Tabs.get_page()}
        """
        page = self[ name ]
        page.label = value
    # __setitem__()
# Tabs


class Table( _EGWidget ):
    """Data table.

    Each column should have only one type, it will be checked.
    Can be accessed as a python list:

    >>> t = Table( 't', 'table', [ 1, 2, 3 ] )
    >>> t[ 0 ]
    [ 1 ]
    >>> del t[ 1 ]
    >>> t[ : ]
    [ 1, 3 ]
    """
    spacing = 3


    class Row( object ):
        # Used to hide gtk.ListStore
        def __init__( self, items ):
            self.__items = items
        # __init__()


        def __str__( self ):
            return "[" + ", ".join( [ str( x ) for x in self.__items ] ) + "]"
        # __str__()
        __repr__ = __str__


        def __len__( self ):
            return len( self.__items )
        # __len__()


        def __nonzero__( self ):
            return self.__items.__nonzero__()
        # __nonzero__()


        def __getitem__( self, index ):
            return self.__items[ index ]
        # __getitem__()


        def __setitem__( self, index, value ):
            self.__items[ index ] = value
        # __setitem__()


        def __delitem__( self, index ):
            del self.__items[ index ]
        # __delitem__()


        def __contains__( self, element ):
            return element in self.__items
        # __contains__()


        def __getslice__( self, start, end ):
            slice = []

            l = len( self.__items )
            while start < 0:
                start += l
            while end < 0:
                end += l

            start = min( start, l )
            end = min( end, l ) # l[ : ] -> l[ 0 : maxlistindex ]

            for i in xrange( start, end ):
                slice.append( self.__items[ i ] )
            return slice
        # __getslice__()


        def __setslice__( self, start, end, items ):
            l = len( self.__items )
            while start < 0:
                start += l
            while end < 0:
                end += l

            start = min( start, l )
            end = min( end, l ) # l[ : ] -> l[ 0 : maxlistindex ]

            l2 = len( items )
            if end - start > l2:
                end = start + l2

            if self.__items.model._hid_row_changed is not None:
                hid_changed = self.__items.model._hid_row_changed
                self.__items.model.handler_block( hid_changed )

            j = 0
            for i in xrange( start, end ):
                self.__items[ i ] = items[ j ]
                j += 1

            if self.__items.model._hid_row_changed is not None:
                hid_changed = self.__items.model._hid_row_changed
                self.__items.model.handler_unblock( hid_changed )
                i = self.__items.iter
                p = self.__items.path
                self.__items.model.row_changed( p, i )

        # __setslice__()
    # Row


    class CellFormat( object ):
        __slots__ = ( "fgcolor", "bgcolor", "font", "bold",
                      "italic", "underline", "strike", "contents" )
        def __init__( self, **kargs ):
            for a in self.__slots__:
                v = kargs.get( a, None )
                setattr( self, a, v )
        # __init__()
    # CellFormat()



    def __init__( self, id, label="", items=None, types=None,
                  headers=None, show_headers=True, editable=False,
                  repositioning=False, expand_columns_indexes=None,
                  hidden_columns_indexes=None, cell_format_func=None,
                  selection_callback=None, data_changed_callback=None,
                  expand_policy=None ):
        """Table constructor.

        @param id: unique identifier.
        @param label: what to show on table frame
        @param items: a list (single column) or list of lists (multiple
               columns)
        @param types: a list of types (str, int, long, float, unicode, bool)
               for columns, if omitted, will be guessed from items.
        @param headers: what to use as table header.
        @param show_headers: whenever to show table headers
        @param editable: if table is editable. If editable, user can change
               values inline or double-clicking, also edit buttons will
               show after the table.
        @param repositioning: allow items to be moved up and down.
        @param expand_columns_indexes: list of indexes that can expand size
        @param cell_format_func: if define, should return a CellFormat with
               properties to be applied to cell. Only non-None properties will
               be used. Function should have the following signature:
                  def func( app, table, row, col, value ):
                      return Table.CellFormat( ... )
               where row and col are indexes in table.
        @param selection_callback: the function (or list of functions) to
               call when selection changes. Function will get as parameters:
                - App reference
                - Table reference
                - List of pairs ( index, row_contents )
        @param data_changed_callback: the function (or list of functions) to
               call when data changes. Function will get as parameters:
                - App reference
                - Table reference
                - Pair ( index, row_contents )
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.

        @warning: although this widget contains data, it's not a
                  _EGDataWidget and thus will not notify application that
                  data changed, also it cannot persist it's data
                  automatically, if you wish, do it manually. This behavior
                  may change in future if Table show to be useful as
                  _EGDataWidget.
        """
        if expand_policy is None:
            expand_policy = ExpandPolicy.All()

        _EGWidget.__init__( self, id, expand_policy=expand_policy )
        self.editable = editable or False
        self.repositioning = repositioning or False
        self.__label = label
        self.headers = headers or tuple()
        self.show_headers = bool( show_headers )
        self.cell_format_func = cell_format_func

        if isinstance( expand_columns_indexes, ( int, long ) ):
            expand_columns_indexes = ( expand_columns_indexes, )
        elif isinstance( expand_columns_indexes, ( tuple, list ) ):
            expand_columns_indexes = tuple( expand_columns_indexes )
        elif expand_columns_indexes is None:
            expand_columns_indexes = tuple()
        else:
            raise ValueError( \
                "expand_columns_indexes must be a sequence of integers" )
        self.expand_columns_indexes = expand_columns_indexes

        if isinstance( hidden_columns_indexes, ( int, long ) ):
            hidden_columns_indexes = ( hidden_columns_indexes, )
        elif isinstance( hidden_columns_indexes, ( tuple, list ) ):
            hidden_columns_indexes = tuple( hidden_columns_indexes )
        elif hidden_columns_indexes is None:
            hidden_columns_indexes = tuple()
        else:
            raise ValueError( \
                "hidden_columns_indexes must be a sequence of integers" )
        self.hidden_columns_indexes = hidden_columns_indexes

        if not ( types or items ):
            raise ValueError( "Must provide items or types!" )
        elif not types:
            items = items or []
            if not isinstance( items[ 0 ], ( list, tuple ) ):
                # just one column, convert to generic representation
                items = [ [ i ] for i in items ]

            types = [ type( i ) for i in items[ 0 ] ]
        self.types = types
        self.items = items

        self.selection_callback = _callback_tuple( selection_callback )
        self.data_changed_callback = _callback_tuple( data_changed_callback )

        self.__setup_gui__()

        self._model._hid_row_changed = None
        self._model._hid_row_deleted = None
        self._model._hid_row_inserted = None
        self.__setup_connections__()
        self.__setup_items__()
    # __init__()


    def __setup_gui__( self ):
        self._vbox = gtk.VBox( False, self.spacing )
        self._vbox.set_border_width( self.spacing )
        self._vbox.set_name( "vbox-%s" % self.id )

        if self.label is not None:
            self._frame = gtk.Frame( self.label )
            self._frame.set_name( self.id )
            self._frame.add( self._vbox )
            root = self._frame
        else:
            root = self._vbox
        self._widgets = ( root, )

        self.__setup_table__()

        if self.editable or self.repositioning:
            self._hbox = gtk.HBox( False, self.spacing )
            self._vbox.pack_start( self._hbox, expand=False, fill=True )

        if self.editable:
            self._btn_add  = gtk.Button( stock=gtk.STOCK_ADD )
            self._btn_del  = gtk.Button( stock=gtk.STOCK_REMOVE )
            self._btn_edit = gtk.Button( stock=gtk.STOCK_EDIT )

            self._hbox.pack_start( self._btn_add )
            self._hbox.pack_start( self._btn_del )
            self._hbox.pack_start( self._btn_edit )

        if self.repositioning:
            if self.editable:
                self._hbox.pack_start( gtk.VSeparator() )

            self._btn_up   = gtk.Button( stock=gtk.STOCK_GO_UP )
            self._btn_down = gtk.Button( stock=gtk.STOCK_GO_DOWN )

            self._btn_up.set_sensitive( False )
            self._btn_down.set_sensitive( False )

            self._hbox.pack_start( self._btn_up )
            self._hbox.pack_start( self._btn_down )
    # __setup_gui__()


    def __setup_connections__( self ):
        if self.data_changed_callback:
            self.__setup_connections_changed__()

        if self.editable:
            self.__setup_connections_editable__()

        if self.repositioning:
            self.__setup_connections_repositioning__()

        if self.selection_callback:
            self.__setup_connections_selection__()
    # __setup_connections__()


    def __setup_connections_changed__( self ):
        def row_changed( model, path, itr ):
            index = path[ 0 ]
            v = ( index, Table.Row( model[ path ] ) )
            for c in self.data_changed_callback:
                c( self.app, self, v )
        # row_changed()


        def row_deleted( model, path ):
            index = path[ 0 ]
            v = ( index, None )
            for c in self.data_changed_callback:
                c( self.app, self, v )
        # row_deleted()

        c = self._model.connect
        self._model._hid_row_changed = c( "row-changed", row_changed )
        self._model._hid_row_deleted = c( "row-deleted", row_deleted )
        self._model._hid_row_inserted = c( "row-inserted", row_changed)
    # __setup_connections_changed__()


    def __setup_connections_editable__( self ):
        def edit_dialog( data ):
            title = "Edit data from table %s" % ( self.label or self.id )
            buttons = ( gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT )
            d = gtk.Dialog( title=title,
                            flags=gtk.DIALOG_MODAL,
                            buttons=buttons )
            d.set_default_response( gtk.RESPONSE_ACCEPT )

            l = len( data )
            t = gtk.Table( l, 2 )
            t.set_border_width( 0 )
            w = {}
            for i, v in enumerate( data ):
                if i in self.hidden_columns_indexes:
                    continue

                title = self._table.get_column( i ).get_title()
                label = gtk.Label( "%s:" % title )
                label.set_justify( gtk.JUSTIFY_RIGHT )
                label.set_alignment( xalign=1.0, yalign=0.5 )

                tp = self.types[ i ]
                if   tp == bool:
                    entry = gtk.CheckButton()
                    entry.set_active( data[ i ] )
                elif tp in ( int, long ):
                    entry = gtk.SpinButton( digits=0 )
                    adj = entry.get_adjustment()
                    adj.lower = Spin.default_min
                    adj.upper = Spin.default_max
                    adj.step_increment = 1
                    adj.page_increment = 5
                    entry.set_value( data[ i ] )
                elif tp == float:
                    entry = gtk.SpinButton( digits=6 )
                    adj = entry.get_adjustment()
                    adj.lower = Spin.default_min
                    adj.upper = Spin.default_max
                    adj.step_increment = 1
                    adj.page_increment = 5
                    entry.set_value( data[ i ] )
                elif tp in ( str, unicode ):
                    entry = gtk.Entry()
                    entry.set_text( data[ i ] )
                elif tp == Image:
                    entry = gtk.Image()
                    entry.set_from_pixbuf( data[ i ].__get_gtk_pixbuf__() )
                else:
                    entry = gtk.Label( str( data[ i ] ) )

                t.attach( label, 0, 1, i, i + 1,
                          xoptions=gtk.FILL,
                          xpadding=self.spacing, ypadding=self.spacing )
                t.attach( entry, 1, 2, i, i + 1,
                          xoptions=gtk.EXPAND|gtk.FILL,
                          xpadding=self.spacing, ypadding=self.spacing )
                w[ i ] = entry

            t.show_all()

            sw = gtk.ScrolledWindow()
            sw.add_with_viewport( t )
            sw.get_child().set_shadow_type( gtk.SHADOW_NONE )
            d.vbox.pack_start( sw )
            # Hack, disable scrollbars so we get the window to the
            # best size
            sw.set_policy( hscrollbar_policy=gtk.POLICY_NEVER,
                           vscrollbar_policy=gtk.POLICY_NEVER )
            d.show_all()
            # Scrollbars are automatic
            sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                           vscrollbar_policy=gtk.POLICY_AUTOMATIC )

            r = d.run()
            d.destroy()
            if r in ( gtk.RESPONSE_REJECT, gtk.RESPONSE_DELETE_EVENT ) :
                return None
            else:
                result = []
                for i in xrange( len( data ) ):
                    tp = self.types[ i ]

                    if i not in w:
                        r = data[ i ]
                    else:
                        wid = w[ i ]

                        if   tp == bool:
                            r = bool( wid.get_active() )
                        elif tp in ( int, long ):
                            r = tp( wid.get_value() )
                        elif tp == float:
                            r = float( wid.get_value() )
                        elif tp in ( str, unicode ):
                            r = tp( wid.get_text() )
                        else:
                            r = data[ i ]
                    result.append( r )

                return result
        # edit_dialog()


        def clicked_add( button ):
            entry = []
            for i, t in enumerate( self.types ):
                if   t == bool:
                    v = False
                elif t in ( int, long, float ):
                    v = 0
                elif t in ( str, unicode ):
                    v = ''
                else:
                    try:
                        v = t.default_value()
                    except AttributeError:
                        try:
                            name = t.__name__
                        except:
                            name = t
                        raise ValueError( ( "Unsuported column (%d) type: %s."
                                            " Type should provide "
                                            "default_value() static method." )
                                          % ( i, name ) )
                entry.append( v )
            result = edit_dialog( entry )
            if result:
                self.append( result )
        # clicked_add()


        def clicked_edit( button ):
            selected = self.selected()
            if not selected:
                return

            for index, data in selected:
                print data
                result = edit_dialog( data )
                if result:
                    self[ index ] = result
        # clicked_edit()


        def clicked_del( button ):
            selected = self.selected()
            if not selected:
                return

            for index, data in selected:
                del self[ index ]
        # clicked_del()

        self._btn_add.connect( "clicked", clicked_add )
        self._btn_del.connect( "clicked", clicked_del )
        self._btn_edit.connect( "clicked", clicked_edit )

        def row_activated( treeview, path, column ):
            data = treeview.get_model()[ path ]
            result = edit_dialog( data )
            if result:
                self[ path[ 0 ] ] = result
        # row_activated()


        self._table.connect( "row-activated", row_activated )
    # __setup_connections_editable__()


    def __setup_connections_repositioning__( self ):
        def selection_changed( selection ):
            result = self.selected()
            if not result:
                self._btn_up.set_sensitive( False )
                self._btn_down.set_sensitive( False )
            else:
                path = result[ 0 ][ 0 ]
                if path > 0:
                    self._btn_up.set_sensitive( True )
                else:
                    self._btn_up.set_sensitive( False )
                if path < len( self ) - 1:
                    self._btn_down.set_sensitive( True )
                else:
                    self._btn_down.set_sensitive( False )
        # selection_changed()

        def move_up( button ):
            result = self.selected()
            a = result[ 0 ][ 0 ]
            if a <= 0:
                return

            b = a - 1
            la = list( self[ a ] )
            lb = list( self[ b ] )
            self[ a ] = lb
            self[ b ] = la
            self.select( b )
        # move_up()

        def move_down( button ):
            result = self.selected()
            a = result[ 0 ][ 0 ]
            if a >= len( self ) - 1:
                return

            b = a + 1
            la = list( self[ a ] )
            lb = list( self[ b ] )
            self[ a ] = lb
            self[ b ] = la
            self.select( b )
        # move_down()

        selection = self._table.get_selection()
        selection.connect( "changed", selection_changed )
        self._btn_up.connect( "clicked", move_up )
        self._btn_down.connect( "clicked", move_down )
    # __setup_connections_repositioning__()


    def __setup_connections_selection__( self ):
        def selection_changed( selection ):
            result = self.selected()
            for c in self.selection_callback:
                c( self.app, self, result )
        # selection_changed()

        selection = self._table.get_selection()
        selection.connect( "changed", selection_changed )
    # __setup_connections_selection__()


    def __create_column_cell_format_func__( self, col, cell_rend ):
        def get_color( c ):
            return Canvas.__to_gtk_color__( Canvas.__color_from__( c ))
        # get_color()

        def func( column, cell_renderer, model, itr, col_idx ):
            row_idx = model.get_path( itr )[ 0 ]
            value = model.get_value( itr, col_idx )
            cf = self.cell_format_func( self.app, self,
                                        row_idx, col_idx, value )
            if cf is None:
                cf = Table.CellFormat()

            bgcolor = cf.bgcolor
            if bgcolor is not None:
                bgcolor = get_color( bgcolor )
            else:
                bgcolor = self._table.style.base[ gtk.STATE_NORMAL ]
            cell_renderer.set_property( "cell-background-gdk",
                                        bgcolor )

            if isinstance( cell_renderer, gtk.CellRendererText ):
                v = None
                if cf.contents is not None:
                    v = model[ itr ][ col_idx ]

                    if callable( cf.contents ):
                        v = cf.contents( v )
                    else:
                        v = cf.contents

                if callable( cell_renderer.model_view_conv ):
                    if v is None:
                        v = model[ itr ][ col_idx ]
                    v = cell_renderer.model_view_conv( v )

                if v is not None:
                    cell_renderer.set_property( "text", v )

                font = cf.font
                if font is not None:
                    font = pango.FontDescription( font )
                else:
                    font = self._table.style.font_desc
                cell_renderer.set_property( "font-desc", font )

                fgcolor = cf.fgcolor
                if fgcolor is not None:
                    fgcolor = get_color( fgcolor )
                else:
                    fgcolor = self._table.style.text[ gtk.STATE_NORMAL ]
                cell_renderer.set_property( "foreground-gdk", fgcolor )

                if cf.underline:
                    underline = pango.UNDERLINE_SINGLE
                else:
                    underline = pango.UNDERLINE_NONE
                cell_renderer.set_property( "underline", underline )

                if cf.bold:
                    bold = pango.WEIGHT_BOLD
                else:
                    bold = pango.WEIGHT_NORMAL
                cell_renderer.set_property( "weight", bold )

                if cf.italic:
                    italic = pango.STYLE_ITALIC
                else:
                    italic = pango.STYLE_NORMAL
                cell_renderer.set_property( "style", italic )

                cell_renderer.set_property( "strikethrough",
                                            bool( cf.strike ) )

            elif isinstance( cell_renderer, gtk.CellRendererToggle ):
                v = None
                if cf.contents is not None:
                    v = model[ itr ][ col_idx ]

                    if callable( cf.contents ):
                        v = cf.contents( v )
                    else:
                        v = cf.contents

                if callable( cell_renderer.model_view_conv ):
                    if v is None:
                        v = model[ itr ][ col_idx ]
                    v = cell_renderer.model_view_conv( v )

                if v is not None:
                    cell_renderer.set_property( "active", v )

            elif isinstance( cell_renderer, gtk.CellRendererPixbuf ):
                v = None
                if cf.contents is not None:
                    v = model[ itr ][ col_idx ]

                    if callable( cf.contents ):
                        v = cf.contents( v )
                    else:
                        v = cf.contents

                if callable( cell_renderer.model_view_conv ):
                    if v is None:
                        v = model[ itr ][ col_idx ]
                    v = cell_renderer.model_view_conv( v )

                if v is not None:
                    cell_renderer.set_property( "pixbuf", v )
        # func()
        return func
    # __create_column_cell_format_func__()


    def __setup_table__( self ):
        self.__setup_model__()
        self._table = gtk.TreeView( self._model )
        self._table.set_name( "table-%s" % self.id )
        self._table.get_selection().set_mode( gtk.SELECTION_MULTIPLE )

        def column_clicked( column ):
            cid, order = self._model.get_sort_column_id()
            self._model.set_sort_column_id( cid, order )
        # column_clicked()

        def toggled( cell_render, path, col ):
            self._model[ path ][ col ] = not self._model[ path ][ col ]
        # toggled()


        def edited( cell_render, path, text, col ):
            t = self.types[ col ]
            try:
                value = t( text )
            except ValueError, e:
                name = t.__name__
                error( "Invalid contents for column of type '%s': %s" %
                       ( name, text ) )
            else:
                self._model[ path ][ col ] = value
        # edited()


        for i, t in enumerate( self.types ):
            if   t == bool:
                cell_rend = gtk.CellRendererToggle()
                props = { "active": i }
                cell_rend.model_view_conv = None
                if self.editable:
                    cell_rend.set_property( "activatable", True)
                    cell_rend.connect( "toggled", toggled, i )

            elif t in ( int, long, float, str, unicode ):
                cell_rend = gtk.CellRendererText()
                props = { "text": i }
                cell_rend.model_view_conv = None
                if self.editable:
                    cell_rend.set_property( "editable", True )
                    cell_rend.connect( "edited", edited, i )

                if t in ( int, long, float ):
                    cell_rend.set_property( "xalign", 1.0 )
            elif t == Image:
                cell_rend = gtk.CellRendererPixbuf()
                cell_rend.model_view_conv = lambda x: x.__get_gtk_pixbuf__()
                props = {}
            else:
                cell_rend = gtk.CellRendererText()
                props = {}
                cell_rend.model_view_conv = str

            try:
                title = self.headers[ i ]
            except IndexError:
                title = "Col-%d (%s)" % ( i, t.__name__ )

            col = gtk.TreeViewColumn( title, cell_rend, **props )
            col.set_resizable( True )
            col.set_sort_column_id( i )
            col.connect( "clicked", column_clicked )

            if self.cell_format_func:
                f = self.__create_column_cell_format_func__( col, cell_rend )
                col.set_cell_data_func( cell_rend, f, i )

            elif callable( cell_rend.model_view_conv ):
                def f( column, cell_rend, model, iter, model_idx ):
                    o = model[ iter ][ model_idx ]
                    v = cell_rend.model_view_conv( o )
                    if   isinstance( cell_rend, gtk.CellRendererText ):
                        cell_rend.set_property( "text", v )
                    elif isinstance( cell_rend, gtk.CellRendererToggle ):
                        cell_rend.set_property( "active", v )
                    elif isinstance( cell_rend, gtk.CellRendererPixbuf ):
                        cell_rend.set_property( "pixbuf", v )
                # f()
                col.set_cell_data_func( cell_rend, f, i )


            if i in self.expand_columns_indexes:
                col.set_expand( True )
            else:
                col.set_expand( False )

            if i not in self.hidden_columns_indexes:
                col.set_visible( True )
            else:
                col.set_visible( False )

            self._table.append_column( col )


        self._table.set_headers_visible( self.show_headers )
        self._table.set_headers_clickable( True )
        self._table.set_reorderable( self.repositioning )
        self._table.set_enable_search( True )

        self._sw = gtk.ScrolledWindow()
        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )
        self._sw.set_shadow_type( gtk.SHADOW_IN )
        self._sw.add( self._table )
        self._vbox.pack_start( self._sw )
    # __setup_table__()


    def __setup_items__( self ):
        if self.items:
            for row in self.items:
                self.append( row, select=False, autosize=False )
            self.columns_autosize()
    # __setup_items__()



    def __setup_model__( self ):
        gtk_types = []
        for i, t in enumerate( self.types ):
            if   t == bool:
                gtk_types.append( gobject.TYPE_BOOLEAN )
            elif t == int:
                gtk_types.append( gobject.TYPE_INT )
            elif t == long:
                gtk_types.append( gobject.TYPE_LONG )
            elif t == float:
                gtk_types.append( gobject.TYPE_FLOAT )
            elif t in ( str, unicode ):
                gtk_types.append( gobject.TYPE_STRING )
            else:
                gtk_types.append( gobject.TYPE_PYOBJECT )

        self._model = gtk.ListStore( *gtk_types )

        def sort_fn( model, itr1, itr2, id ):
            return cmp( model[ itr1 ][ id ], model[ itr2 ][ id ] )
        # sort_fn()

        for i in xrange( len( self.types ) ):
            self._model.set_sort_func( i, sort_fn, i )
    # __setup_model__()


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        self._frame.set_label( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )


    def columns_autosize( self ):
        self._table.columns_autosize()
    # columns_autosize()


    def select( self, index ):
        selection = self._table.get_selection()
        selection.unselect_all()
        selection.select_path( index )
    # select()


    def selected( self ):
        model, paths = self._table.get_selection().get_selected_rows()
        if paths:
            result = []
            for p in paths:
                result.append( ( p[ 0 ], Table.Row( model[ p ] ) ) )
            return result
        else:
            return None
    # selected()


    def append( self, row, select=True, autosize=True ):
        if not isinstance( row, ( list, tuple ) ):
            row = ( row, )

        if self._model._hid_row_inserted is not None:
            self._model.handler_block( self._model._hid_row_inserted )
        if self._model._hid_row_changed is not None:
            self._model.handler_block( self._model._hid_row_changed )
        itr = self._model.append( row )
        if self._model._hid_row_changed is not None:
            self._model.handler_unblock( self._model._hid_row_changed )
        if self._model._hid_row_inserted is not None:
            self._model.handler_unblock( self._model._hid_row_inserted )

        self._model.row_changed( self._model.get_path( itr ), itr )

        if autosize:
            self._table.columns_autosize()
        if select:
            self._table.set_cursor( self._model[ itr ].path )
    # append()


    def insert( self, index, row, select=True, autosize=True ):
        if not isinstance( row, ( list, tuple ) ):
            row = ( row, )

        if self._model._hid_row_inserted is not None:
            self._model.handler_block( self._model._hid_row_inserted )
        if self._model._hid_row_changed is not None:
            self._model.handler_block( self._model._hid_row_changed )
        itr = self._model.insert( index, row )
        if self._model._hid_row_changed is not None:
            self._model.handler_unblock( self._model._hid_row_changed )
        if self._model._hid_row_inserted is not None:
            self._model.handler_unblock( self._model._hid_row_inserted )

        self._model.row_changed( self._model.get_path( itr ), itr )

        if autosize:
            self._table.columns_autosize()
        if select:
            self._table.set_cursor( self._model[ itr ].path )
    # insert()


    def __nonzero__( self ):
        return self._model.__nonzero__()
    # __nonzero__()

    def __len__( self ):
        return len( self._model )
    # __len__()


    def __iadd__( self, other ):
        self.append( other )
        return self
    # __iadd__()


    def __setitem__( self, index, other ):
        if not isinstance( other, ( list, tuple, Table.Row ) ):
            other = ( other, )
        try:
            if self._model._hid_row_inserted is not None:
                self._model.handler_block( self._model._hid_row_inserted )
            if self._model._hid_row_changed is not None:
                self._model.handler_block( self._model._hid_row_changed )
            self._model[ index ] = other
            if self._model._hid_row_changed is not None:
                self._model.handler_unblock( self._model._hid_row_changed )
            if self._model._hid_row_inserted is not None:
                self._model.handler_unblock( self._model._hid_row_inserted )

            p = ( index, )
            self._model.row_changed( p, self._model.get_iter( p ) )

        except TypeError, e:
            raise IndexError( "index out of range" )
    # __setitem__()


    def __getitem__( self, index ):
        try:
            items = self._model[ index ]
        except TypeError, e:
            raise IndexError( "index out of range" )

        return Table.Row( items )
    # __getitem__()


    def __delitem__( self, index ):
        try:
            del self._model[ index ]
        except TypeError, e:
            raise IndexError( "index out of range" )
    # __delitem__()


    def __contains__( self, row ):
        for r in self._model:
            if row in r:
                return True
        return False
    # __contains__()


    def __getslice__( self, start, end ):
        slice = []

        l = len( self._model )
        while start < 0:
            start += l
        while end < 0:
            end += l

        start = min( start, l )
        end = min( end, l ) # l[ : ] -> l[ 0 : maxlistindex ]

        for i in xrange( start, end ):
            slice.append( Table.Row( self._model[ i ] ) )
        return slice
    # __getslice__()


    def __setslice__( self, start, end, slice ):
        l = len( self._model )
        while start < 0:
            start += l
        while end < 0:
            end += l

        del self[ start : end ]

        # just insert len( slice ) items
        l2 = len( slice )
        if end - start > l2:
            end = start + l2
        for j, i in enumerate( xrange( start, end ) ):
            row = list( slice[ j ] )


            # extend row if necessary
            lr = len( row )
            lt = len( self.types )
            if lr < lt:
                for i in xrange( lr, lt ):
                    t = self.types[ i ]
                    row.append( t() )

            self.insert( i, row, select=False, autosize=False )
    # __setslice__()


    def __delslice__( self, start, end ):
        l = len( self._model )
        while start < 0:
            start += l
        while end < 0:
            end += l

        start = min( start, l )
        end = min( end, l ) # l[ : ] -> l[ 0 : maxlistindex ]

        while end > start:
            end -= 1
            del self._model[ end ]
    # __delslice__()
# Table


class RichText( _EGWidget ):
    """A Rich Text viewer

    Display text with basic formatting instructions. Formatting is
    done using a HTML subset.
    """

    class Renderer( gtk.TextView ):
        """Specialized TextView to render formatted texts.

        This class emits "follow-link" when user clicks somewhere.

        It implements Writer interface as specified in standard library
        "formatter" module.
        """
        bullet = None
        margin = 2
        signal_created = False

        def __init__( self, link_color="#0000ff",
                      foreground=None, background=None,
                      resource_provider=None ):
            """RichText.Renderer constructor.

            @param link_color: color to use with links. String with color name
                   or in internet format (3 pairs of RGB, in hexa, prefixed by
                   #).
            @param foreground: default foreground color. Same spec as
                   link_color.
            @param background: default background color. Same spec as
                   link_color.
            @param resource_provider: function to provide unresolved resources.
                   If some image could not be handled as a file, this function
                   will be called and it should return an gtk.gdk.Pixbuf.
                   Since http://url.com/file will always be unresolved, you
                   may use this to provide remote file access to this class.
            """
            self.link_color = link_color or "#0000ff"
            self.foreground = foreground
            self.background = background
            self.resource_provider = resource_provider
            self.hovering_over_link = False

            b = gtk.TextBuffer()
            gtk.TextView.__init__( self, b )

            self.set_cursor_visible( False )
            self.set_editable( False )
            self.set_wrap_mode( gtk.WRAP_WORD )
            self.set_left_margin( self.margin )
            self.set_right_margin( self.margin )

            self.__setup_connections__()
            self.__setup_render__()
            self.__create_bullets__()
        # __init__()


        def __create_bullets__( self ):
            klass = RichText.Renderer
            if klass.bullet is None:
                width = height = 16
                dx = dy = 4

                colormap = gtk.gdk.colormap_get_system()
                visual = colormap.get_visual()

                white = colormap.alloc_color( "#ffffff", True, True )
                black = colormap.alloc_color( "#000000", True, True )

                pixmap = gtk.gdk.Pixmap( None, width, height, visual.depth )
                white_gc = pixmap.new_gc( foreground=white, background=black,
                                          fill=gtk.gdk.SOLID, line_width=1,
                                          line_style=gtk.gdk.LINE_SOLID )
                black_gc = pixmap.new_gc( foreground=black, background=white,
                                          fill=gtk.gdk.SOLID, line_width=1,
                                          line_style=gtk.gdk.LINE_SOLID )
                pixmap.draw_rectangle( white_gc, True, 0, 0, width, height )
                pixmap.draw_arc( black_gc, True, dx, dy,
                                 width - dx * 2, height - dy * 2,
                                 0, 23040 )


                pixbuf = gtk.gdk.Pixbuf( gtk.gdk.COLORSPACE_RGB, True, 8,
                                         width, height )
                pixbuf = pixbuf.get_from_drawable( pixmap, colormap, 0, 0, 0, 0,
                                                   width, height )
                pixbuf = pixbuf.add_alpha( True, chr(255), chr(255), chr(255) )
                klass.bullet = pixbuf
        # __create_bullets__()


        def __setup_connections__( self ):
            hand_cursor = gtk.gdk.Cursor( gtk.gdk.HAND2 )
            regular_cursor = gtk.gdk.Cursor( gtk.gdk.XTERM )
            K_Return = gtk.gdk.keyval_from_name( "Return" )
            K_KP_Enter = gtk.gdk.keyval_from_name( "KP_Enter" )
            K_Home = gtk.gdk.keyval_from_name( "Home" )
            K_End = gtk.gdk.keyval_from_name( "End" )

            if not self.__class__.signal_created:
                gobject.signal_new( "follow-link", RichText.Renderer,
                                    gobject.SIGNAL_RUN_LAST,
                                    gobject.TYPE_NONE,
                                    ( gobject.TYPE_STRING,
                                      gobject.TYPE_ULONG ) )
                self.__class__.signal_created = True


            def get_link( itr ):
                tags = itr.get_tags()
                for tag in tags:
                    href = tag.get_data( "href" )
                    if href is not None:
                        return href
                return None
            # get_link()

            def follow_if_link( text_view, itr ):
                href = get_link( itr )
                if href:
                    self.emit( "follow-link", href, itr.get_offset() )
            # follow_if_link()

            def key_press_event( text_view, event ):
                if event.keyval in ( K_Return, K_KP_Enter ):
                    b = text_view.get_buffer()
                    itr = b.get_iter_at_mark( b.get_insert() )
                    follow_if_link( text_view, itr )
                elif event.keyval == K_Home:
                    itr = text_view.get_buffer().get_start_iter()
                    text_view.scroll_to_iter( itr, 0.0, False )
                elif event.keyval == K_End:
                    itr = text_view.get_buffer().get_end_iter()
                    text_view.scroll_to_iter( itr, 0.0, False )
            # key_press_event()
            self.connect( "key-press-event", key_press_event )

            def event_after( text_view, event ):
                if event.type != gtk.gdk.BUTTON_RELEASE:
                    return False

                if event.button != 1:
                    return False

                b = text_view.get_buffer()

                # we shouldn't follow a link if the user has selected something
                try:
                    start, end = b.get_selection_bounds()
                except ValueError:
                    pass
                else:
                    if start.get_offset() != end.get_offset():
                        return False

                x, y = text_view.window_to_buffer_coords( gtk.TEXT_WINDOW_WIDGET,
                                                          int( event.x ),
                                                          int( event.y ) )
                itr = text_view.get_iter_at_location( x, y )
                follow_if_link( text_view, itr )
                return False
            # event_after()
            self.connect( "event-after", event_after )

            def set_cursor_if_appropriate( text_view, x, y ):
                b = text_view.get_buffer()
                itr = text_view.get_iter_at_location( x, y )

                self.hovering_over_link = get_link( itr )
                if self.hovering_over_link:
                    cursor = hand_cursor
                else:
                    cursor = regular_cursor

                win = text_view.get_window( gtk.TEXT_WINDOW_TEXT )
                win.set_cursor( cursor )
            # set_cursor_if_appropriate()

            def motion_notify_event( text_view, event ):
                x, y = text_view.window_to_buffer_coords( gtk.TEXT_WINDOW_WIDGET,
                                                          int( event.x ),
                                                          int( event.y ) )
                set_cursor_if_appropriate( text_view, x, y )
                text_view.window.get_pointer()
                return False
            # motion_notify_event()
            self.connect( "motion-notify-event", motion_notify_event )

            def visibility_notify_event( text_view, event ):
                wx, wy, mod = text_view.window.get_pointer()
                x, y = text_view.window_to_buffer_coords( gtk.TEXT_WINDOW_WIDGET,
                                                          wx, wy )
                set_cursor_if_appropriate( text_view, x, y )
                return False
            # visibility_notify_event()
            self.connect( "visibility-notify-event", visibility_notify_event )


            def after_realize( text_view ):
                colormap = self.get_colormap()
                if self.background:
                    bg = colormap.alloc_color( self.background, True, True )
                    w = text_view.get_window( gtk.TEXT_WINDOW_TEXT )
                    w.set_background( bg )
                    w = text_view.get_window( gtk.TEXT_WINDOW_WIDGET )
                    w.set_background( bg )
            # after_realize()
            self.connect_after( "realize", after_realize )
        # __setup_connections__()


        def __setup_render__( self ):
            self.buffer = self.get_buffer()
            itr = self.buffer.get_start_iter()

            k = {}
            if self.foreground:
                k[ "foreground" ] = self.foreground

            create_tag = self.buffer.create_tag
            self.tags = {
                "default": create_tag( "default", **k ),
                "bold": create_tag( "bold", weight=pango.WEIGHT_BOLD ),
                "italic": create_tag( "italic", style=pango.STYLE_ITALIC ),
                "link": create_tag( "link", foreground=self.link_color,
                                    underline=pango.UNDERLINE_SINGLE ),
                "h1": create_tag( "h1", scale=pango.SCALE_XX_LARGE ),
                "h2": create_tag( "h2", scale=pango.SCALE_X_LARGE ),
                "h3": create_tag( "h3", scale=pango.SCALE_LARGE ),
                "monospaced": create_tag( "monospaced", font="monospace" ),
                }
            self.tags[ "default" ].set_priority( 0 )

            self.font = []
            self.link = []
            self.margin = []
        # __setup_render__()


        def send_paragraph( self, blankline ):
            if blankline:
                self.send_flowing_data( "\n" )
        # send_paragraph()


        def send_line_break( self ):
            self.send_paragraph( 1 )
        # send_line_break()


        def send_flowing_data( self, data ):
            itr = self.buffer.get_end_iter()
            t = [ self.tags[ "default" ] ] + self.font + self.link
            self.buffer.insert_with_tags( itr, data, *t )
        # send_flowing_data()

        def send_literal_data( self, data ):
            itr = self.buffer.get_end_iter()
            t = [ self.tags[ "default" ], self.tags[ "monospaced" ] ] + \
                self.font + self.link
            self.buffer.insert_with_tags( itr, data, *t )
        # send_literal_data()


        def send_hor_rule( self ):
            itr = self.buffer.get_end_iter()
            anchor = self.buffer.create_child_anchor( itr )
            w = gtk.HSeparator()
            def size_allocate( widget, rect ):
                lm = self.get_left_margin()
                rm = self.get_right_margin()
                width = max( rect.width - lm - rm - 1, 0 )
                w.set_size_request( width, -1 )
            # size_allocate()

            self.connect_after( "size-allocate", size_allocate )
            self.add_child_at_anchor( w, anchor )
        # send_hor_rule()


        def new_margin( self, margin, level ):
            itr = self.buffer.get_end_iter()
            self.margin.append( ( margin, level ) )
        # new_margin()


        def send_label_data( self, data ):
            itr = self.buffer.get_end_iter()
            t = self.font + self.link + [ self.tags[ "bold" ] ]

            margin, level = self.margin[ -1 ]
            self.buffer.insert_with_tags( itr, '\t' * level, *t )
            if data == '*' and self.bullet:
                self.buffer.insert_pixbuf( itr, self.bullet )
            else:
                self.buffer.insert_with_tags( itr, data, *t )
            self.buffer.insert_with_tags( itr, ' ', *t )
        # send_label_data()


        def add_image( self, filename, width, height ):
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file( filename )
            except gobject.GError:
                if self.resource_provider:
                    pixbuf = self.resource_provider( filename )
                else:
                    raise ValueError( "No resource provider for %r" % filename)

            if not pixbuf:
                self.send_flowing_data( "[%s]" % filename )
                return

            ow = pixbuf.get_width()
            oh = pixbuf.get_height()
            p = float( ow ) / float( oh )

            if width > 0 and height < 1:
                height = int( width / p )
            elif height > 0 and width < 1:
                width = int( height * p )
            if width > 0 and height > 0:
                pixbuf = pixbuf.scale_simple( width, height,
                                              gtk.gdk.INTERP_BILINEAR )
            itr = self.buffer.get_end_iter()
            self.buffer.insert_pixbuf( itr, pixbuf )
        # add_image()


        def start_link( self, url, name=None ):
            t = self.buffer.create_tag()
            t.set_data( "href", url )
            if name:
                self.buffer.create_mark( name,
                                         self.buffer.get_end_iter(), True )
            self.link = [ self.tags[ "link" ], t ]
        # new_link()


        def end_link( self ):
            self.link = []
        # end_link()


        def new_font( self, font ):
            if isinstance( font, ( tuple, list ) ):
                def append_unique( v ):
                    f = self.font
                    if v not in f:
                        f.append( v )
                # append

                size, is_italic, is_bold, is_tt = font
                if   size == "h1":
                    append_unique( self.tags[ "h1" ] )
                elif size == "h2":
                    append_unique( self.tags[ "h2" ] )
                elif size == "h3":
                    append_unique( self.tags[ "h3" ] )

                if is_italic:
                    append_unique( self.tags[ "italic" ] )
                if is_bold:
                    append_unique( self.tags[ "bold" ] )

            elif isinstance( font, dict ):
                t = {}
                family = font.get( "family" )
                size = font.get( "size" )
                color = font.get( "color" )
                background = font.get( "bgcolor" )
                if family:
                    t[ "family" ] = family
                if size:
                    t[ "size-points" ] = int( size )
                if color:
                    t[ "foreground" ] = color
                if background:
                    t[ "background" ] = background
                self.font.append( self.buffer.create_tag( None, **t ) )
            else:
                self.font = []
        # new_font()


        def goto( self, anchor ):
            mark = self.buffer.get_mark( anchor )
            if mark is not None:
                self.scroll_mark_onscreen( mark )
            else:
                raise ValueError( "Inexistent anchor: %r" % anchor )
        # goto()


        def reset( self ):
            a = self.buffer.get_start_iter()
            b = self.buffer.get_end_iter()
            self.buffer.delete( a, b )
        # reset()
    # Renderer


    class Parser( htmllib.HTMLParser ):
        """HTML subset parser"""
        def anchor_bgn( self, href, name, type ):
            htmllib.HTMLParser.anchor_bgn( self, href, name, type )
            self.formatter.push_link( href, name )
        # anchor_bgn()


        def anchor_end( self ):
            self.formatter.pop_link()
        # anchor_end()


        def handle_image( self, source, alt, ismap, align, width, height ):
            self.formatter.add_image( source, width, height )
        # handle_image()


        def start_font( self, attrs ):
            k = dict( attrs )
            self.formatter.push_font( k )
        # start_font()


        def end_font( self ):
            self.formatter.pop_font()
        # end_font()
    # Parser


    class Formatter( formatter.AbstractFormatter ):
        """HTML subset formatter"""
        def add_image( self, filename, width, height ):
            self.writer.add_image( filename, width, height )
        # add_image()

        def push_link( self, url, name ):
            self.writer.start_link( url, name )
        # push_link()

        def pop_link( self ):
            self.writer.end_link()
        # pop_link()


        def push_font( self, font ):
            if isinstance( font, dict ):
                self.writer.new_font( font )
            else:
                formatter.AbstractFormatter.push_font( self, font )
        # push_font()
    # Formatter

    bgcolor = _gen_ro_property( "bgcolor" )
    fgcolor = _gen_ro_property( "fgcolor" )
    link_color = _gen_ro_property( "link_color" )
    padding = 5

    def __init__( self, id, text="", label=None, link_color="blue",
                  fgcolor=None, bgcolor=None, callback=None,
                  img_provider=None, expand_policy=None ):
        """RichText constructor.

        @param id: unique identifier.
        @param text: text to use in this viewer.
        @param label: label to display in the widget frame around the viewer.
               If None, no label or frame will be shown.
        @param link_color: color to use for links.
        @param fgcolor: color to use for foreground (text)
        @param bgcolor: color to use for background.
        @param callback: function (or list of functions) to call when
               user clicks a link. Links to anchor will automatically make
               the anchor/mark visible and then callback. Function will get
               as parameters:
                - App reference
                - RichText reference
                - href contents (string)
                - offset from buffer begin (integer)
        @param img_provider: if images could not be resolved, call this
               function. It should get an address (string) and return an
               eagle.Image. Eagle already provides a handle to addresses
               prefixed with "eagle://", the following part should be an
               eagle.Image id, and the image should be live (not garbage
               collected) when displaying it, so remember to keep a
               reference to it! You may use img_provider to download
               files from webservers and stuff like that.
               Function signature:
                  def img_provider( filename ):
                      return eagle.Image( ... )
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        _EGWidget.__init__( self, id, expand_policy )
        self.__label = label
        self._callback = _callback_tuple( callback )
        self.link_color = link_color
        self.foreground = fgcolor
        self.background = bgcolor
        self.img_provider = img_provider

        self.__setup_gui__()
        self.__setup_parser__()
        self.__setup_connections__()
        self.set_text( text )
    # __init__()


    def __setup_gui__( self ):
        def img_provider( filename ):
            img = None
            if filename.startswith( "eagle://" ):
                id = filename[ len( "eagle://" ) : ]
                img = Image.__get_by_id__( id )
            elif self.img_provider:
                img = self.img_provider( filename )

            if img:
                return img.__get_gtk_pixbuf__()
            else:
                error( "Could not find image %r" % filename )
        # img_provider()

        self._sw = gtk.ScrolledWindow()
        self._renderer = RichText.Renderer( link_color=self.link_color,
                                            foreground=self.fgcolor,
                                            background=self.bgcolor,
                                            resource_provider=img_provider )

        self._sw.set_border_width( self.padding )
        self._sw.set_shadow_type( gtk.SHADOW_IN )
        if self.label is not None:
            self._frame = gtk.Frame( self.label )
            self._frame.add( self._sw )
            root = self._frame
            self._frame.set_shadow_type( gtk.SHADOW_OUT )
        else:
            root = self._sw

        self._sw.add( self._renderer )
        self._sw.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC )
        self._sw.show_all()
        self._widgets = ( root, )
    # __setup_gui__()


    def __setup_parser__( self ):
        self._formatter = RichText.Formatter( self._renderer )
        self._parser = RichText.Parser( self._formatter )
    # __setup_parser__()


    def __setup_connections__( self ):
        def callback( text_view, href, offset ):
            if href.startswith( "#" ):
                try:
                    text_view.goto( href[ 1 : ] )
                except ValueError, e:
                    error( str( e ) )

            for c in self._callback:
                c( self.app, self, href, offset )
        # callback()
        self._renderer.connect( "follow-link", callback )
    # __setup_connections__()


    def set_text( self, text ):
        """Replace current text"""
        self._text = text
        self._renderer.reset()
        self.__setup_parser__()
        self._parser.feed( self.text )
    # set_text()


    def get_text( self ):
        """Return current text, with formatting tags"""
        return self._text
    # get_text()

    text = property( get_text, set_text )


    def append( self, text ):
        self._text += text
        self._parser.feed( text )
    # append()


    def set_label( self, label ):
        if self.__label is None:
            raise ValueError( "You cannot change label of widget created "
                              "without one. Create it with placeholder! "
                              "(label='')" )
        self.__label = label
        self._frame.set_label( self.__label )
    # set_label()


    def get_label( self ):
        return self.__label
    # get_label()

    label = property( get_label, set_label )


    def __str__( self ):
        return "%s( id=%r, label=%r, link_color=%r, fgcolor=%r, bgcolor=%r )"%\
               ( self.__class__.__name__, self.id, self.label, self.link_color,
                 self.fgcolor, self.bgcolor )
    # __str__()
    __repr__ = __str__
# RichText


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
        "media:play",
        "media:pause",
        "media:stop",
        "media:previous",
        "media:next",
        "media:forward",
        "media:rewind",
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
        "media:play": gtk.STOCK_MEDIA_PLAY,
        "media:pause": gtk.STOCK_MEDIA_PAUSE,
        "media:stop": gtk.STOCK_MEDIA_STOP,
        "media:previous": gtk.STOCK_MEDIA_PREVIOUS,
        "media:next": gtk.STOCK_MEDIA_NEXT,
        "media:forward": gtk.STOCK_MEDIA_FORWARD,
        "media:rewind": gtk.STOCK_MEDIA_REWIND,
        }

    def __init__( self, id, label="", stock=None, callback=None,
                  expand_policy=None ):
        """Push button constructor.

        @param label: what text to show, if stock isn't provided.
        @param stock: optional. One of L{stock_items}.
        @param callback: the function (or list of functions) to call
               when button is pressed. Function will get as parameter:
                - App reference
                - Button reference
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        if expand_policy is None:
            expand_policy = ExpandPolicy.Fill()
        self.label = label
        self.stock = stock
        self.callback = _callback_tuple( callback )

        # Check if provided stock items are implemented
        for i in self.stock_items:
            if i not in self._gtk_stock_map:
                print >> sys.stderr, \
                      "Stock item %s missing in implementation map!" % ( i, )

        _EGWidget.__init__( self, id, expand_policy=expand_policy )

        self.__setup_gui__()
        self.__setup_connections__()
    # __init__()


    def __setup_gui__( self ):
        k = {}
        try:
            k[ "stock" ] = self._gtk_stock_map[ self.stock ]
        except KeyError, e:
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
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        def show_about( app_id, wid_id ):
            self.app.show_about_dialog()
        # show_about()
        Button.__init__( self, id or self.__get_id__(),
                         stock="about", callback=show_about,
                         expand_policy=expand_policy )
    # __init__()
# AboutButton


class CloseButton( Button, AutoGenId ):
    """Push button to close L{App}."""
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        def close( app_id, wid_id ):
            self.app.close()
        # close()
        Button.__init__( self, id or self.__get_id__(),
                         stock="close", callback=close,
                         expand_policy=expand_policy )
    # __init__()
# CloseButton


class QuitButton( Button, AutoGenId ):
    """Push button to quit all L{App}s."""
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        def c( app_id, wid_id ):
            quit()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="quit", callback=c,
                         expand_policy=expand_policy )
    # __init__()
# QuitButton


class HelpButton( Button, AutoGenId ):
    """Push button to show L{HelpDialog} of L{App}."""
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        def c( app_id, wid_id ):
            self.app.show_help_dialog()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="help", callback=c,
                         expand_policy=expand_policy )
    # __init__()
# HelpButton


class OpenFileButton( Button, AutoGenId ):
    """Push button to show dialog to choose an existing file."""
    def __init__( self, id=None, filename=None,
                  filter=None, multiple=False,
                  callback=None, expand_policy=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param filename: default filename.
        @param filter: filter files to show, see L{FileChooser}.
        @param multiple: enable selection of multiple files.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - file name or file list (if multiple).
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( action=FileChooser.ACTION_OPEN,
                                       filename=filename,
                                       filter=filter, multiple=multiple )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c,
                         expand_policy=expand_policy )
    # __init__()
# OpenFileButton


class SelectFolderButton( Button, AutoGenId ):
    """Push button to show dialog to choose an existing folder/directory."""
    def __init__( self, id=None, filename=None, callback=None,
                  expand_policy=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param filename: default filename.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - directory/folder name.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( action=FileChooser.ACTION_SELECT_FOLDER,
                                       filename=filename )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c,
                         expand_policy=expand_policy )
    # __init__()
# SelectFolderButton


class SaveFileButton( Button, AutoGenId ):
    """Push button to show dialog to choose a file to save."""
    def __init__( self, id=None, filename=None,
                  filter=None, callback=None, expand_policy=None ):
        """Constructor.

        @param id: may not be provided, it will be generated automatically.
        @param filename: default filename.
        @param filter: filter files to show, see L{FileChooser}.
        @param callback: function (or list of functions) to call back
               when file is selected. Function will get as parameters:
                - app reference.
                - widget reference.
                - file name.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.

        @see: L{FileChooser}
        """
        def c( app_id, wid_id ):
            f = self.app.file_chooser( action=FileChooser.ACTION_SAVE,
                                       filename=filename,
                                       filter=filter )
            if f is not None and callback:
                callback( self.app, self, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="save", callback=c,
                         expand_policy=expand_policy )
    # __init__()
# SaveFileButton


class PreferencesButton( Button, AutoGenId ):
    """Push button to show L{PreferencesDialog} of L{App}."""
    def __init__( self, id=None, expand_policy=None ):
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
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        _EGWidget.__init__( self, id or self.__get_id__(),
                            expand_policy=expand_policy )
        self._wid = gtk.HSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# HSeparator


class VSeparator( _EGWidget ):
    """Horizontal separator"""
    def __init__( self, id=None, expand_policy=None ):
        """You may not provide id, it will be generated automatically"""
        _EGWidget.__init__( self, id or self.__get_id__(),
                            expand_policy=expand_policy )
        self._wid = gtk.VSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# VSeparator


class Label( _EGDataWidget, AutoGenId ):
    """Text label"""
    label = _gen_ro_property( "label" )

    LEFT   = 0.0
    RIGHT  = 1.0
    CENTER = 0.5
    TOP    = 0.0
    MIDDLE = 0.5
    BOTTOM = 1.0

    def __init__( self, id=None, label="",
                  halignment=LEFT, valignment=MIDDLE, expand_policy=None ):
        """Label constructor.

        @param id: may not be provided, it will be generated automatically.
        @param label: what this label will show.
        @param halignment: horizontal alignment, like L{LEFT}, L{RIGHT} or
               L{CENTER}.
        @param valignment: vertical alignment, like L{TOP}, L{BOTTOM} or
               L{MIDDLE}.
        @param expand_policy: how this widget should fit space, see
               L{ExpandPolicy.Policy.Rule}.
        """
        if expand_policy is None:
            expand_policy = ExpandPolicy.Nothing()

        _EGDataWidget.__init__( self, id or self.__get_id__(), False,
                                expand_policy=expand_policy )
        self.label = label

        self._wid = gtk.Label( self.label )
        self._wid.set_name( self.id )
        self._wid.set_alignment( xalign=halignment, yalign=valignment )
        self._widgets = ( self._wid, )
    # __init__()


    def get_value( self ):
        return self._wid.get_text()
    # get_value()


    def set_value( self, value ):
        self._wid.set_text( str( value ) )
    # set_value()


    def __str__( self ):
        return "%s( id=%r, label=%r )" % \
               ( self.__class__.__name__, self.id, self.label )
    # __str__()
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
