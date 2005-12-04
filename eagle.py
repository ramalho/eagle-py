#!/usr/bin/env python2

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

__author__ = "Gustavo Sverzut Barbieri"
__author_email__ = "barbieri@gmail.com"
__license__ = "LGPL"


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
    ]

import os
import sys
import gc
import pygtk
pygtk.require( "2.0" )
import gtk
import pango
import cPickle as pickle

required_gtk = ( 2, 4, 0 )
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
        if not self.children:
            return

        n = len( self.children )

        if self.horizontal:
            self.resize( 2, n )
        else:
            self.resize( n, 2 )

        for idx, c in enumerate( self.children ):
            w = c.get_widgets()
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


    def get_widgets( self ):
        return self.children
    # get_widgets()
# _Table


class _Panel( gtk.ScrolledWindow ):
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


    def get_widgets( self ):
        return self._tab.get_widgets()
    # get_widgets()
# _Panel


class _VPanel( _Panel ):
    _horizontal = False
    _hscrollbar_policy = gtk.POLICY_NEVER
    _vscrollbar_policy = gtk.POLICY_AUTOMATIC
# _VPanel


class _HPanel( _Panel ):
    _horizontal = True
    _hscrollbar_policy = gtk.POLICY_AUTOMATIC
    _vscrollbar_policy = gtk.POLICY_NEVER
# _HPanel


class _EGObject( object ):
    id = _gen_ro_property( "id" )

    def __init__( self, id ):
        self.id = id
    # __init__()
# _EGObject


class AutoGenId( object ):
    last_id_num = 0

    def __get_id__( classobj ):
        n = "%s-%d" % ( classobj.__name__, classobj.last_id_num )
        classobj.last_id_num += 1
        return n
    # __get_id__()
    __get_id__ = classmethod( __get_id__ )
# AutoGenId


class Image( _EGObject, AutoGenId ):
    def __init__( self, **kargs ):
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
        else:
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
        return gtk.gdk.pixbuf_get_formats()
    # get_formats()


    def get_writable_formats( self ):
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

        If no value is provided as has_alpha, then it's set to False if
        depth is less or equal 24 or set to True if depth is 32.

        If no value is provided as rowstride, then it's set to
        width * depth / bits_per_sample.
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


    def get_n_channels( self ):
        return self._img.get_n_channels()
    # get_n_channels()


    def get_bytes_per_pixel( self ):
        return self.get_n_channels() * self._img.get_bits_per_sample()
    # get_bytes_per_pixel()


    def has_alpha( self ):
        return self._img.get_has_alpha()
    # has_alpha()
# Image



class _EGWidget( _EGObject ):
    app = _gen_ro_property( "app" )
    persistent = False
    can_persist = False

    def __init__( self, id, persistent, app=None ):
        _EGObject.__init__( self, id )
        if app is not None:
            self.app = app
        self.persistent = persistent
        self._widgets = tuple()
    # __init__()


    def __get_resize_mode__( self ):
        "Return a tuple with ( horizontal, vertical ) resize mode"
        return ( gtk.FILL, gtk.FILL )
    # __get_resize_mode__()


    def get_widgets( self ):
        return self._widgets
    # get_widgets()


    def set_active( self, active=True ):
        for w in self.get_widgets():
            w.set_sensitive( active )
    # set_active()


    def set_inactive( self ):
        self.set_active( False )
    # set_inactive()


    def show( self ):
        for w in self.get_widgets():
            w.show()
    # show()


    def hide( self ):
        for w in self.get_widgets():
            w.hide()
    # hide()


    def set_value( self, value ):
        raise NotImplementedError
    # set_value()


    def get_value( self ):
        raise NotImplementedError
    # get_value()
# _EGWidget


class AboutDialog( _EGWidget ):
    def __init__( self, app,
                  title, author=None, description=None, help=None,
                  version=None, license=None, copyright=None ):
        self.app = app
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
        self._diag.set_default_size( 400, 300 )
        _set_icon_list( self._diag, gtk.STOCK_ABOUT )

        self._sw = gtk.ScrolledWindow()
        self._diag.get_child().pack_start( self._sw, expand=True, fill=True )

        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )

        self._text = gtk.TextView()
        self._sw.add( self._text )
        self._text.set_editable( False )
        self._text.set_cursor_visible( False )
        self._text.set_wrap_mode( gtk.WRAP_WORD )

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


class HelpDialog( _EGWidget ):
    def __init__( self, app, title, help=None ):
        self.app = app
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
        self._diag.set_default_size( 400, 300 )
        _set_icon_list( self._diag, gtk.STOCK_HELP )

        self._sw = gtk.ScrolledWindow()
        self._diag.get_child().pack_start( self._sw, expand=True, fill=True )

        self._sw.set_policy( hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy=gtk.POLICY_AUTOMATIC )

        self._text = gtk.TextView()
        self._sw.add( self._text )
        self._text.set_editable( False )
        self._text.set_cursor_visible( False )
        self._text.set_wrap_mode( gtk.WRAP_WORD )

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


class FileChooser( _EGObject ):
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
        self.app = app
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
    def __init__( self, app, children ):
        self.id = self.__get_id__()
        self.app = app
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
            if w.can_persist:
                w.persistent = True
            self.app.__add_widget__( w )
    # __add_widgets_to_app__()


    def run( self ):
        self._diag.show_all()
        self._diag.run()
        self._diag.hide()
    # run()
# PreferencesDialog


class DebugDialog( _EGObject ):
    # Most of DebugDialog code came from Gazpacho code! Thanks!
    border = 12
    spacing = 6

    def __init__( self ):
        self.__setup_gui__()
    # __init__()


    def __setup_gui__( self ):
        b = ( gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE )
        self._diag = gtk.Dialog( "Application Crashed!",
                                 parent=None,
                                 flags=gtk.DIALOG_MODAL,
                                 buttons=b )
        self._diag.set_border_width( self.border )
        self._diag.set_default_size( 600, 400 )

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
        if r == gtk.RESPONSE_CLOSE:
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


class _EGWidLabelEntry( _EGWidget ):
    """Widget that holds a label and an associated Entry.

    You must setup an instance attribute _entry before using it, since
    this will be set as mnemonic for this label and also returned in
    get_widgets()
    """
    label = _gen_ro_property( "label" )
    can_persist = True

    def __init__( self, id, persistent, label="" ):
        _EGWidget.__init__( self, id, persistent )
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
# _EGWidLabelEntry


class App( _EGObject, AutoGenId ):
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


    def get_widget_by_id( self, widget_id ):
        return self._widgets.get( widget_id, None )
    # get_widget_by_id()


    def show_about_dialog( self ):
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
        diag = HelpDialog( app=self,
                           title=self.title,
                           help=self.help,
                           )
        diag.run()
    # show_help_dialog()


    def file_chooser( self, action, filename=None,
                      filter=None, multiple=False ):
        diag = FileChooser( app=self, action=action,
                            filename=filename, filter=filter,
                            multiple=multiple )
        return diag.run()
    # file_chooser()


    def show_preferences_dialog( self ):
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
            self._widgets[ widget.id ] = widget
            widget.app = self
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

        if self._top.get_widgets():
            self._vbox.pack_start( self._top, expand=False, fill=True )
            if self._center.get_widgets() or self._bottom.get_widgets():
                self._vbox.pack_start( gtk.HSeparator(), expand=False,
                                       fill=True )

        if self._center.get_widgets():
            self._vbox.pack_start( self._center, expand=True, fill=True )

        if self._bottom.get_widgets():
            if self._center.get_widgets():
                self._vbox.pack_start( gtk.HSeparator(), expand=False,
                                       fill=True )
            self._vbox.pack_start( self._bottom, expand=False, fill=True )

        if self._left.get_widgets():
            self._hbox.pack_start( self._left,  expand=False, fill=True )
            if self._center.get_widgets() or self._top.get_widgets or \
               self._bottom.get_widgets() or self._right.get_widgets():
                self._hbox.pack_start( gtk.VSeparator(),
                                       expand=False, fill=False )

        self._hbox.pack_start( self._vbox,  expand=True, fill=True )

        if self._right.get_widgets():
            if self._center.get_widgets() or self._top.get_widgets or \
               self._bottom.get_widgets():
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


    def data_changed( self, widget_id, value ):
        self.save()
        for c in self.data_changed_callback:
            c( self.id, widget_id, value )
    # data_changed()


    def __delete_event__( self, *args ):
        self.save()
        for c in self.quit_callback:
            c( self.id )

        del _apps[ self.id ]
        if not _apps:
            gtk.main_quit()
    # __delete_event__()


    def __persistence_filename__( self ):
        return "%s.save_data" % self.id
    # __persistence_filename__()


    def save( self ):
        d = {}
        for id, w in self._widgets.iteritems():
            if w.persistent:
                d[ id ] = w.get_value()

        f = open( self.__persistence_filename__(), "wb" )
        pickle.dump( d, f, pickle.HIGHEST_PROTOCOL )
        f.close()
    # save()


    def load( self ):
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
            if w and w.persistent:
                w.set_value( v )
    # load()


    def close( self ):
        self.__delete_event__()
        self._win.destroy()
    # close()
# App


class Canvas( _EGWidget ):
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
        _EGWidget.__init__( self, id, False )
        self.label = label

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
                    c( self.app.id, self.id, event.button,
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
                    c( self.app.id, self.id, 1, x, y )

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
        gc = self.__configure_gc__( fgcolor=color )
        self._pixmap.draw_point( gc, x, y )
        self._area.queue_draw_area( x, y, 1, 1 )
    # draw_point()


    def draw_points( self, points, color=None ):
        gc = self.__configure_gc__( fgcolor=color )
        self._pixmap.draw_points( gc, points )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_poinst()


    def draw_line( self, x0, y0, x1, y1, color=None, size=1 ):
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_line( gc, x0, y0, x1, y1 )

        w, h = abs( x1 - x0 ) + 1, abs( y1 - y0 ) + 1
        x, y = min( x0, x1 ), min( y0, y1 )
        self._area.queue_draw_area( x, y, w, h )
    # draw_line()


    def draw_segments( self, segments, color=None, size=1 ):
        """Draw line segments."""
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_segments( gc, segments )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_segments()


    def draw_lines( self, points, color=None, size=1 ):
        """Draw lines connecting points.

        First and last points are not connected, use draw_polygon
        to do that
        """
        gc = self.__configure_gc__( fgcolor=color, line_width=size )
        self._pixmap.draw_lines( gc, points )
        w, h = self._pixmap.get_size()
        self._area.queue_draw_area( 0, 0, w, h )
    # draw_lines()


    def draw_rectangle( self, x, y, width, height, color=None, size=1,
                        fillcolor=None, filled=False ):
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

        start and end angles are in radians.
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
        w, h = self._pixmap.get_size()
        img = gtk.gdk.Pixbuf( gtk.gdk.COLORSPACE_RGB, True, 8, w, h )
        img.get_from_drawable( self._pixmap, self._area.get_colormap(),
                               0, 0, 0, 0, w, h )
        return Image( __int_image__=img )
    # get_image()
# Canvas


class Entry( _EGWidLabelEntry ):
    value = _gen_ro_property( "value" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", value="", callback=None,
                  persistent=False ):
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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
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
    def __init__( self, id, label="", value="", callback=None,
                  persistent=False ):
        Entry.__init__( self, id, label, value, callback, persistent )
        self._entry.set_visibility( False )
    # __init__()
# Password


class Spin( _EGWidLabelEntry ):
    value = _gen_ro_property( "value" )
    min = _gen_ro_property( "min" )
    max = _gen_ro_property( "max" )
    step = _gen_ro_property( "step" )
    digits = _gen_ro_property( "digits" )

    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None, digits=3,
                  callback=None, persistent=False ):
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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
        # callback()
        self._entry.connect( "value-changed", callback )
    # __setup_connections__()


    def set_value( self, value ):
        self._entry.set_value( float( value ) )
    # set_value()
# Spin


class IntSpin( Spin ):
    def __init__( self, id, label="",
                  value=None, min=None, max=None, step=None,
                  callback=None, persistent=False ):
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
    def __init__( self, id, label="",
                  value=None, min=0, max=None, step=None,
                  callback=None, persistent=False ):
        if min < 0:
            raise ValueError( "UIntSpin cannot have min < 0!" )
        Spin.__init__( self, id, label, value, min, max, step, 0, callback,
                       persistent )
    # __init__()
# UIntSpin


class Color( _EGWidLabelEntry ):
    color = _gen_ro_property( "color" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", color=0, callback=None,
                  persistent=False ):
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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
        # callback()
        self._entry.connect( "color-set", callback )
    # __setup_connections__()


    def get_value( self ):
        c = self._entry.get_color()
        r = int( c.red   / 65535.0 * 255 )
        g = int( c.green / 65535.0 * 255 )
        b = int( c.blue  / 65535.0 * 255 )
        return ( r, g, b )
    # get_value()


    def set_value( self, value ):
        self._entry.set_color( self.color_from( value ) )
    # set_value()
# Color


class Font( _EGWidLabelEntry ):
    font = _gen_ro_property( "font" )
    callback = _gen_ro_property( "callback" )

    def __init__( self, id, label="", font="sans 12", callback=None,
                  persistent=False ):
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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
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
    options = _gen_ro_property( "options" )
    active = _gen_ro_property( "active" )

    def __init__( self, id, label="", options=None, active=None,
                  callback=None, persistent=False ):
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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
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
    value = _gen_ro_property( "value" )
    can_persist = False

    def __init__( self, id, label="", value=0.0 ):
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
        self._entry.pulse()
    # pulse()
# Progress


class CheckBox( _EGWidget ):
    state = _gen_ro_property( "state" )
    can_persist = True

    def __init__( self, id, label="", state=False, callback=None,
                  persistent=False ):
        self.label = label
        self.state = state
        self.callback = _callback_tuple( callback )

        _EGWidget.__init__( self, id, persistent )

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
            self.app.data_changed( self.id, v )
            for c in self.callback:
                c( self.app.id, self.id, v )
        # callback()
        self._wid.connect( "toggled", callback )
    # __setup_connections__()


    def get_value( self ):
        return self._wid.get_active()
    # get_value()
# CheckBox


class Group( _EGWidget ):
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
        _EGWidget.__init__( self, id, False )
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
    stock = _gen_ro_property( "stock" )
    callback = _gen_ro_property( "callback" )

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
        self.label = label
        self.stock = stock
        self.callback = _callback_tuple( callback )

        _EGWidget.__init__( self, id, False )

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
                c( self.app.id, self.id )
        # callback()
        self._button.connect( "clicked", callback )
    # __setup_connections__()
# Button


class AboutButton( Button, AutoGenId ):
    def __init__( self, id=None ):
        def show_about( app_id, wid_id ):
            self.app.show_about_dialog()
        # show_about()
        Button.__init__( self, id or self.__get_id__(),
                         stock="about", callback=show_about )
    # __init__()
# AboutButton


class CloseButton( Button, AutoGenId ):
    def __init__( self, id=None ):
        def close( app_id, wid_id ):
            self.app.close()
        # close()
        Button.__init__( self, id or self.__get_id__(),
                         stock="close", callback=close )
    # __init__()
# CloseButton


class QuitButton( Button, AutoGenId ):
    def __init__( self, id=None ):
        def c( app_id, wid_id ):
            quit()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="quit", callback=c )
    # __init__()
# QuitButton


class HelpButton( Button, AutoGenId ):
    def __init__( self, id=None ):
        def c( app_id, wid_id ):
            self.app.show_help_dialog()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="help", callback=c )
    # __init__()
# HelpButton


class OpenFileButton( Button, AutoGenId ):
    def __init__( self, id=None,
                  filter=None, multiple=False,
                  callback=None ):
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_OPEN,
                                       filter=filter, multiple=multiple )
            if f is not None and callback:
                callback( self.app.id, self.id, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c )
    # __init__()
# OpenFileButton


class SelectFolderButton( Button, AutoGenId ):
    def __init__( self, id=None, callback=None ):
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_SELECT_FOLDER )
            if f is not None and callback:
                callback( self.app.id, self.id, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="open", callback=c )
    # __init__()
# SelectFolderButton


class SaveFileButton( Button, AutoGenId ):
    def __init__( self, id=None, filename=None,
                  filter=None, callback=None ):
        def c( app_id, wid_id ):
            f = self.app.file_chooser( FileChooser.ACTION_SAVE,
                                       filename=filename,
                                       filter=filter )
            if f is not None and callback:
                callback( self.app.id, self.id, f )
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="save", callback=c )
    # __init__()
# SaveFileButton


class PreferencesButton( Button, AutoGenId ):
    def __init__( self, id=None ):
        def c( app_id, wid_id ):
            f = self.app.show_preferences_dialog()
        # c()
        Button.__init__( self, id or self.__get_id__(),
                         stock="preferences", callback=c )
    # __init__()
# PreferencesButton


class HSeparator( _EGWidget, AutoGenId ):
    def __init__( self, id=None ):
        _EGWidget.__init__( self, id or self.__get_id__(), False )
        self._wid = gtk.HSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# HSeparator


class VSeparator( _EGWidget ):
    def __init__( self, id=None ):
        _EGWidget.__init__( self, id or self.__get_id__(), False )
        self._wid = gtk.VSeparator()
        self._wid.set_name( self.id )
        self._widgets = ( self._wid, )
    # __init__()
# VSeparator


class Label( _EGWidget, AutoGenId ):
    label = _gen_ro_property( "label" )

    LEFT   = 0.0
    RIGHT  = 1.0
    CENTER = 0.5
    TOP    = 0.0
    MIDDLE = 0.5
    BOTTOM = 1.0

    def __init__( self, id=None, label="",
                  halignment=LEFT, valignment=MIDDLE ):
        _EGWidget.__init__( self, id or self.__get_id__(), False )
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



def run():
    try:
        gtk.main()
    except KeyboardInterrupt:
        raise SystemExit( "User quit using Control-C" )
# run()

def quit():
    gtk.main_quit()
# quit()


def get_app_by_id( app_id ):
    if app_id is None:
        try:
            return _apps.values()[ 0 ]
        except IndexError, e:
            raise ValueError( "No application defined!" )
    else:
        try:
            return _apps[ app_id ]
        except KeyError, e:
            raise ValueError( "Application id \"%s\" doesn't exists!" % \
                              app_id )
# get_app_by_id()


def get_widget_by_id( widget_id, app_id=None ):
    if app_id is None or isinstance( app_id, ( str, unicode) ):
        app = get_app_by_id( app_id )
    elif isinstance( app_id, App ):
        app = app_id
    else:
        raise ValueError( "app_id must be string or App instance!" )
    if app:
        w = app.get_widget_by_id( widget_id )
        if not w:
            raise ValueError( "Widget id \"%s\" doesn't exists!" % widget_id )
        else:
            return w
# get_widget_by_id()


def get_value( widget_id, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        return wid.get_value()
    except ValueError, e:
        raise ValueError( e )
# get_value()


def set_value( widget_id, value, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_value( value )
    except ValueError, e:
        raise ValueError( e )
# set_value()


def show( widget_id, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.show()
    except ValueError, e:
        raise ValueError( e )
# show()


def hide( widget_id, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.hide()
    except ValueError, e:
        raise ValueError( e )
# hide()


def set_active( widget_id, active=True, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_active( active )
    except ValueError, e:
        raise ValueError( e )
# set_active()


def set_inactive( widget_id, app_id=None ):
    try:
        wid = get_widget_by_id( widget_id, app_id )
        wid.set_inactive()
    except ValueError, e:
        raise ValueError( e )
# set_inactive()


def close( app_id=None ):
    try:
        app = get_app_by_id( app_id )
        app.close()
    except ValueError, e:
        raise ValueError( e )
# close()
