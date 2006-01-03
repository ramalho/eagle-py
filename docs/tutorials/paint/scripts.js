var browser = null;

function whichBrowser() {
    an = navigator.appName;
    prod = navigator.product;
    if ( an.indexOf( "Microsoft" ) >= 0 )
	{  return "ie"; }
    else if ( ( prod == "Gecko" ) || ( an.indexOf( "Netscape" ) >= 0 ) )
	{ return "mozilla"; }
    else if ( an.indexOf( "Konqueror" ) >= 0 )
	{ return "konqueror"; }
    else { return "unknow"; }
}
browser = whichBrowser();

if ( document.getElementById ) {


    function getElement( e ) {
	return document.getElementById( e )
	    }


    function getStyle( e ) {
	return getElement( e ).style;
    }


    function hide( e ) {
	getStyle( e ).display="none";
    }


    function unhide( e ) {
	getStyle( e ).display="block";
    }


    function setOpacity( e, v ) {
	v = parseFloat( v );
	if ( browser == "mozilla" ) {
	    getStyle( e ).opacity = v;
	} else if ( browser == "konqueror" ) {
	    getStyle( e ).KhtmlOpacity = v;
	} else if ( browser == "ie" ) {
	    getElement( e ).filters.alpha.opacity = parseInt( v * 100 );
	}
    }


    function toggleFontStyle( e ) {
	s = getStyle( e );
	if ( s.fontStyle != "italic" ) {
	    s.fontStyle = "italic";
	} else {
	    s.fontStyle = "normal";
	}
    }

    function toggleFontWeight( e ) {
	s = getStyle( e );
	if ( s.fontWeight != "bold" ) {
	    s.fontWeight = "bold";
	} else {
	    s.fontWeight = "normal";
	}
    }

    function toggleBorder( e ) {
	s = getStyle( e );
	if ( s.borderStyle.indexOf( "dotted" ) < 0 ) {
	    s.borderStyle = "dotted";
	    s.borderWidth = "1px";
	} else {
	    s.borderStyle = "none";
	    s.borderWidth = "1px";
	}
    }

    function fadeOut( e, v ) {
	if ( v == undefined ) v = 1.0;
	v = parseFloat( v ) - 0.2
	    setOpacity( e, v );
	if ( v > 0 ) {
	    setTimeout( 'fadeOut( "' + e + '", ' + v + ' ) ', 30 );
	} else {
	    hide( e );
	}
    }

    function fadeIn( e, v ) {
	if ( v == undefined ) v = 0.0;
	v = parseFloat( v ) + 0.2
	    setOpacity( e, v );
	if ( v < 1.0 ) {
	    setTimeout( 'fadeIn( "' + e + '", ' + v + ' ) ', 30 );
	}
    }


    function toggle( e ) {
	if ( getStyle( e ).display != "none" )
	    {
		fadeOut( e );
	    }
	else {
	    unhide( e );
	    fadeIn( e );
	}
    }


    function hToggle( h ) {
	toggleFontStyle( "h-" + h );
	toggle( h );
    }


    function imgToggle( img ) {
	toggleFontStyle( "caption-" + img );
	toggleFontWeight( "caption-" + img );
	toggle( "img-" + img );
	toggleBorder( "div-" + img );
    }

    function listingToggle( listing ) {
	toggleFontStyle( "caption-" + listing );
	toggleFontWeight( "caption-" + listing );
	toggleBorder( "caption-" + listing );
	toggle( listing );
    }

} else {



    function showoff() {
	window.alert( "Your browser (" + navigator.appName +
		      ") doesn't support getElementById()!" );
	return true;
    }
    function hide( e ) {
	showoff();
    }
    function show( e ) {
	showoff();
    }
    function setOpacity( e, v ) {
	showoff();
    }
    function imgToggle( e ) {
	showoff();
    }
    function listingToggle( e ) {
	showoff();
    }

}
