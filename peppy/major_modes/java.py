# peppy Copyright (c) 2006-2008 Rob McMullen
# Licenced under the GPLv2; see http://peppy.flipturn.org for more info
"""Java programming language editing support.

Major mode for editing Java files.
"""

import os

import wx
import wx.stc

from peppy.lib.foldexplorer import *
from peppy.lib.autoindent import CStyleAutoindent
from peppy.yapsy.plugins import *
from peppy.major import *
from peppy.fundamental import FundamentalMode

class JavaMode(SimpleCLikeFoldFunctionMatchMixin, FundamentalMode):
    """Major mode for editing Java files.
    """
    keyword = 'Java'
    
    icon = 'icons/page_white_cup.png'
    regex = "(\.java)$"
    
    default_classprefs = (
       )
    
    autoindent = CStyleAutoindent()


class JavaModePlugin(IPeppyPlugin):
    """Plugin to register Java mode and user interface.
    """
   
    def getMajorModes(self):
        yield JavaMode