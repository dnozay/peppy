#!/usr/bin/env python

"""
peppy - (ap)Proximated (X)Emacs Powered by Python.

An experiment using the modern software development process.

This is a wxPython/Scintilla-based editor written in and extensible
through Python. It attempts to provide an XEmacs-like multi-window,
multi-tabbed interface using the Advanced User Interface (wx.aui)
framework of wxPython.

The program is designed around the emacs idea of major modes and minor
modes, and further extends this with global plugins.  In writing the
editor, I also borrowed quite a lot from emacs terminology, including
frames and buffers, the minibuffer concept, and the keyboard bindings.

I did not borrow emacs lisp, however; that being the primary reason
for me wanting to move away from emacs.  I find it easy to think in
Python, unlike lisp which my brain can't seem to flush fast enough
after learning just enough to hack XEmacs.

Plugins
=======

There are currently two plugin types that can be used to extend peppy:
L{ProtocolPlugin<plugin.ProtocolPlugin>}s and
L{IMajorModeMatcher<plugin.IMajorModeMatcher>}s.

@author: $author
@version: $version
"""

# setup.py requires that these be defined, and the OnceAndOnlyOnce
# principle is used here.  This is the only place where these values
# are defined in the source distribution, and everything else that
# needs this should grab it from here.
__version__ = "svn-devel"
__author__ = "Rob McMullen"
__author_email__ = "robm@users.sourceforge.net"
__url__ = "http://www.flipturn.org/peppy/"
__download_url__ = "http://www.flipturn.org/peppy/archive/"
__description__ = "(ap)Proximated (X)Emacs Powered by Python"
__keywords__ = "text editor, wxwindows, scintilla"
__license__ = "GPL"

from peppy.main import Peppy, run, main

from peppy.buffers import Buffer, BufferHooks, BufferFrame, BufferApp
from peppy.configprefs import *
from peppy.debug import debuglog, dprint, debugmixin
from peppy.iconstorage import *
from peppy.major import MajorMode, MajorAction
from peppy.minor import MinorMode, IMinorModeProvider, \
     MinorModeIncompatibilityError

__all__ = [ 
    'Peppy', 'run', 'main',
    'Buffer', 'BufferHooks', 'BufferFrame', 'BufferApp',
    'HomeConfigDir', 'GlobalSettings', 'ClassSettingsMixin',
            'getSubclassHierarchy',
    'debuglog','dprint','debugmixin',
    'getIconStorage','getIconBitmap',
    'MajorMode', 'MajorAction',
    'MinorMode', 'IMinorModeProvider', 'MinorModeIncompatibilityError',
    ]
#print __all__
