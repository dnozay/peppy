import os

import wx
import wx.stc as stc

from menudev import *
from buffers import *
from views import *
from trac.core import *
from debug import *


class OpenFundamental(FrameAction):
    name = "&Open Sample Text"
    tooltip = "Open some sample text"
    icon = wx.ART_FILE_OPEN

##    def isEnabled(self, state=None):
##        return not self.frame.isOpen()

    def action(self, state=None, pos=-1):
        self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        self.frame.open("about:demo.txt")

class WordWrap(FrameToggle):
    name = "&Word Wrap"
    tooltip = "Toggle word wrap in this view"
    icon = wx.ART_TOOLBAR

    def isEnabled(self, state=None):
        return True
    
    def isChecked(self, index):
        viewer=self.frame.getCurrentViewer()
        if viewer:
            return viewer.settings.wordwrap
        return False
    
    def action(self, state=None, pos=-1):
        self.dprint("id=%x name=%s" % (id(self),self.name))
        viewer=self.frame.getCurrentViewer()
        if viewer:
            viewer.setWordWrap(not viewer.settings.wordwrap)
    
class LineNumbers(FrameToggle):
    name = "&Line Numbers"
    tooltip = "Toggle line numbers in this view"
    icon = wx.ART_TOOLBAR

    def isEnabled(self, state=None):
        return True
    
    def isChecked(self, index):
        viewer=self.frame.getCurrentViewer()
        if viewer:
            return viewer.settings.linenumbers
        return False
    
    def action(self, state=None, pos=-1):
        self.dprint("id=%x name=%s" % (id(self),self.name))
        viewer=self.frame.getCurrentViewer()
        if viewer:
            viewer.setWordWrap(not viewer.settings.linenumbers)
    
class BeginningOfLine(FrameAction):
    name = "Cursor to Start of Line"
    tooltip = "Move the cursor to the start of the current line."
    keyboard = 'C-A'

    def action(self, state=None, pos=-1):
        self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        viewer=self.frame.getCurrentViewer()
        if viewer:
            s=viewer.stc
            pos = s.GetCurrentPos()
            col = s.GetColumn(pos)
            s.GotoPos(pos-col)
        

class EndOfLine(FrameAction):
    name = "Cursor to End of Line"
    tooltip = "Move the cursor to the end of the current line."
    keyboard = 'C-E'

    def action(self, state=None, pos=-1):
        self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        viewer=self.frame.getCurrentViewer()
        if viewer:
            s=viewer.stc
            line = s.GetCurrentLine()
            s.GotoPos(s.GetLineEndPosition(line))

class FindMinibuffer(Minibuffer):
    def minibuffer(self, viewer):
        from pype import findbar
        self.win=findbar.FindBar(viewer.win,viewer,viewer.stc)
        print "findbar=%s" % self.win

    def focus(self):
        self.win.box1.SetFocus()
    
class ReplaceMinibuffer(FindMinibuffer):
    def minibuffer(self, viewer):
        from pype import findbar
        self.win=findbar.ReplaceBar(viewer.win,viewer,viewer.stc)
    

class FindText(MinibufferAction):
    name = "Find..."
    tooltip = "Search for a string in the text."
    keyboard = 'C-S'
    minibuffer = FindMinibuffer

class ReplaceText(MinibufferAction):
    name = "Replace..."
    tooltip = "Replace a string in the text."
    keyboard = 'F6'
    minibuffer = ReplaceMinibuffer

class GotoLine(MinibufferAction):
    name = "Goto Line..."
    tooltip = "Goto a line in the text."
    keyboard = 'M-G'
    minibuffer = FindMinibuffer




class FundamentalView(View):
    pluginkey = 'fundamental'
    keyword='Fundamental'
    regex=".*"

    defaultsettings={
        'menu_actions':[
            [[('&Edit',0.1)],WordWrap,0.1],
            LineNumbers,
            FindText,
            ReplaceText,
            GotoLine,
            ],
        'keyboard_actions':[
            BeginningOfLine,
            EndOfLine,
            ]
        }


    documents={}

    def __init__(self,buffer,frame):
        View.__init__(self,buffer,frame)

    def createEditWindow(self,parent):
        self.dprint("creating new Fundamental window")
        self.createSTC(parent,style=True)
        win=self.stc
        win.Bind(wx.EVT_KEY_DOWN, self.frame.KeyPressed)
        return win

    def createSTC(self,parent,style=False):
        self.stc=MySTC(parent)
        self.applyDefaultStyle()
        if style:
            self.styleSTC()

    def applyDefaultStyle(self):
        face1 = 'Arial'
        face2 = 'Times New Roman'
        face3 = 'Courier New'
        pb = 10

        # make some styles
        self.stc.StyleSetSpec(stc.STC_STYLE_DEFAULT, "size:%d,face:%s" % (pb, face3))
        self.stc.StyleClearAll()

        # line numbers in the margin
        self.stc.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "size:%d,face:%s" % (pb, face1))
        if self.settings.linenumbers:
            self.stc.SetMarginType(0, stc.STC_MARGIN_NUMBER)
            self.stc.SetMarginWidth(0, 22)
        else:
            self.stc.SetMarginWidth(0,0)
            
        # turn off symbol margin
        if self.settings.symbols:
            self.stc.SetMarginWidth(1, 0)
        else:
            self.stc.SetMarginWidth(1, 16)

        # turn off folding margin
        if self.settings.folding:
            self.stc.SetMarginWidth(2, 16)
        else:
            self.stc.SetMarginWidth(2, 0)

        self.setWordWrap()

    def setWordWrap(self,enable=None):
        if enable is not None:
            self.settings.wordwrap=enable
        if self.settings.wordwrap:
            self.stc.SetWrapMode(stc.STC_WRAP_CHAR)
            self.stc.SetWrapVisualFlags(stc.STC_WRAPVISUALFLAG_END)
        else:
            self.stc.SetWrapMode(stc.STC_WRAP_NONE)

    def setLineNumbers(self,enable=None):
        if enable is not None:
            self.settings.linenumbers=enable
        if self.settings.linenumbers:
            self.stc.SetMarginType(0, stc.STC_MARGIN_NUMBER)
            self.stc.SetMarginWidth(0, 22)
        else:
            self.stc.SetMarginWidth(0,0)

    def styleSTC(self):
        pass

    def openPostHook(self):
        # SetIndent must be called whenever a new document is loaded
        # into the STC
        self.stc.SetIndent(4)
        #self.dprint("indention=%d" % self.stc.GetIndent())

        self.stc.SetIndentationGuides(1)



global_menu_actions=[
    [[('&File',0.0)],OpenFundamental,0.2],
]


class ViewFactory(Component,debugmixin):
    implements(IViewFactory)

    def viewScore(self,buffer):
        return 2

    def getView(self,buffer):
        return FundamentalView


if __name__ == "__main__":
    app=testapp(0)
    frame=RootFrame(app.main)
    frame.Show(True)
    app.MainLoop()

