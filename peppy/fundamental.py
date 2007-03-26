# peppy Copyright (c) 2006-2007 Rob McMullen
# Licenced under the GPL; see http://www.flipturn.org/peppy for more info
import os, shutil

import wx
import wx.stc
from wx.lib.pubsub import Publisher

from peppy import *
from peppy.mainmenu import Paste
from peppy.menu import *

from peppy.actions.minibuffer import *
from peppy.actions.gotoline import *
from peppy.actions.pypefind import *
import peppy.boa as boa

class OpenFundamental(SelectAction):
    name = _("&Open Sample Text")
    tooltip = _("Open some sample text")
    icon = wx.ART_FILE_OPEN

    def action(self, pos=-1):
        assert self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        self.frame.open("about:demo.txt")

class WordWrap(ToggleAction):
    name = _("&Word Wrap")
    tooltip = _("Toggle word wrap in this view")
    icon = wx.ART_TOOLBAR

    def isChecked(self):
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            return viewer.settings.word_wrap
        return False
    
    def action(self, pos=-1):
        assert self.dprint("id=%x name=%s" % (id(self),self.name))
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            viewer.setWordWrap(not viewer.settings.word_wrap)
    
class LineNumbers(ToggleAction):
    name = _("&Line Numbers")
    tooltip = _("Toggle line numbers in this view")
    icon = wx.ART_TOOLBAR

    def isChecked(self):
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            return viewer.settings.line_numbers
        return False
    
    def action(self, pos=-1):
        assert self.dprint("id=%x name=%s" % (id(self),self.name))
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            viewer.setLineNumbers(not viewer.settings.line_numbers)

class Folding(ToggleAction):
    name = _("&Folding")
    tooltip = _("Toggle folding in this view")
    icon = wx.ART_TOOLBAR

    def isChecked(self):
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            return viewer.settings.folding
        return False
    
    def action(self, pos=-1):
        assert self.dprint("id=%x name=%s" % (id(self),self.name))
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            viewer.setFolding(not viewer.settings.folding)

class ScintillaCmdKeyExecute(BufferModificationAction):
    cmd = 0

    def modify(self, mode, pos=-1):
        assert self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        mode.stc.CmdKeyExecute(self.cmd)

class BeginningOfLine(ScintillaCmdKeyExecute):
    name = _("Cursor to Start of Line")
    tooltip = _("Move the cursor to the start of the current line")
    cmd = wx.stc.STC_CMD_HOMEDISPLAY
        
class BeginningTextOfLine(ScintillaCmdKeyExecute):
    name = _("Cursor to first non-blank character in the line")
    tooltip = _("Move the cursor to the start of the current line")
    key_bindings = {'emacs': 'C-A',}
    cmd = wx.stc.STC_CMD_VCHOME
        
class EndOfLine(ScintillaCmdKeyExecute):
    name = _("Cursor to End of Line")
    tooltip = _("Move the cursor to the end of the current line")
    key_bindings = {'emacs': 'C-E',}
    cmd = wx.stc.STC_CMD_LINEEND

class PreviousLine(ScintillaCmdKeyExecute):
    name = _("Cursor to previous line")
    tooltip = _("Move the cursor up a line")
    key_bindings = {'emacs': 'C-P',}
    cmd = wx.stc.STC_CMD_LINEUP

class NextLine(ScintillaCmdKeyExecute):
    name = _("Cursor to next line")
    tooltip = _("Move the cursor down a line")
    key_bindings = {'emacs': 'C-N',}
    cmd = wx.stc.STC_CMD_LINEDOWN


class WordOrRegionMutateMixin(object):
    """Mixin class to operate on a word or the selected region.
    """

    def mutate(self, txt):
        """Operate on specified text and return new text.

        Method designed to be overridden by subclasses to provide the
        text operation desired by the subclass.

        @param txt: input text
        @returns: text resulting from the desired processing
        """
        return txt

    def mutateSelection(self, s):
        """Change the current word or highlighted region.

        Perform some text operation on the current word or region.  If
        a region is active in the STC, use it; otherwise, use the word
        as defined by the text from the current cursor position to the
        end of the word.  The end of the word is defined by the STC's
        STC_CMD_WORDRIGHT.

        The operation is performed by the C{mutate} method, which
        subclasses will override to provide the functionality.

        Side effect: moves the cursor to the end of the region if it
        operated on the region, or to the start of the next word.
        
        @param s: styled text control
        """
        s.BeginUndoAction()
        (pos, end) = s.GetSelection()
        if pos==end:
            s.CmdKeyExecute(wx.stc.STC_CMD_WORDRIGHT)
            end = s.GetCurrentPos()
        word = s.GetTextRange(pos, end)
        s.SetTargetStart(pos)
        s.SetTargetEnd(end)
        s.ReplaceTarget(self.mutate(word))
        s.EndUndoAction()
        s.GotoPos(end)

    def action(self, pos=-1):
        assert self.dprint("id=%x name=%s pos=%s" % (id(self),self.name,str(pos)))
        viewer=self.frame.getActiveMajorMode()
        if viewer:
            self.mutateSelection(viewer.stc)
            
class CapitalizeWord(WordOrRegionMutateMixin, BufferModificationAction):
    """Title-case the current word and move the cursor to the start of
    the next word.
    """

    name = _("Capitalize word")
    tooltip = _("Capitalize current word")
    key_bindings = {'emacs': 'M-C',}

    def mutate(self, txt):
        """Change to title case -- first letter capitalized, rest
        lower case.
        """
        return txt.title()

class UpcaseWord(WordOrRegionMutateMixin, BufferModificationAction):
    """Upcase the current word and move the cursor to the start of the
    next word.
    """

    name = _("Upcase word")
    tooltip = _("Upcase current word")
    key_bindings = {'emacs': 'M-U',}

    def mutate(self, txt):
        """Change to all upper case.
        """
        return txt.upper()

class DowncaseWord(WordOrRegionMutateMixin, BufferModificationAction):
    """Downcase the current word and move the cursor to the start of the
    next word.
    """

    name = _("Downcase word")
    tooltip = _("Downcase current word")
    key_bindings = {'emacs': 'M-L',}

    def mutate(self, txt):
        """Change to all lower case.
        """
        return txt.lower()


class BraceHighlightMixin(object):
    """Brace highlighting mixin for code modes.

    Highlight matching braces or flag mismatched braces.  This is
    called during the EVT_STC_UPDATEUI event handler.

    Code taken from StyledTextCtrl_2 from the wxPython demo.  Should
    probably implement this as a dynamic method of the text control or
    the Major Mode, controllable by a setting.
    """
    def braceHighlight(self):
        s = self.stc

        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = s.GetCurrentPos()

        if caretPos > 0:
            charBefore = s.GetCharAt(caretPos - 1)
            styleBefore = s.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == wx.stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = s.GetCharAt(caretPos)
            styleAfter = s.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == wx.stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = s.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            s.BraceBadLight(braceAtCaret)
        else:
            s.BraceHighlight(braceAtCaret, braceOpposite)
        


class ShiftLeft(ScintillaCmdKeyExecute):
    name = _("Shift &Left")
    tooltip = _("Unindent a line region")
    icon = 'icons/text_indent_remove_rob.png'
    cmd = wx.stc.STC_CMD_BACKTAB

class ShiftRight(ScintillaCmdKeyExecute):
    name = _("Shift &Right")
    tooltip = _("Indent a line or region")
    icon = 'icons/text_indent_rob.png'
    cmd = wx.stc.STC_CMD_TAB


class StandardCommentMixin(debugmixin):
    def comment(self, add=True):
        """Comment or uncomment a region.

        Comment or uncomment a region.

        @param add: True to add comments, False to remove them
        """
        s = self.stc
        eol_len = len(s.getLinesep())
        
        s.BeginUndoAction()
        line, lineend = s.GetLineRegion()
        assert self.dprint("lines: %d - %d" % (line, lineend))
        try:
            selstart, selend = s.GetSelection()
            assert self.dprint("selection: %d - %d" % (selstart, selend))

            start = selstart
            end = s.GetLineEndPosition(line)
            while line <= lineend:
                start = self.commentLine(start, end)
                line += 1
                end = s.GetLineEndPosition(line)
            s.SetSelection(selstart, start - eol_len)
        finally:
            s.EndUndoAction()

class CommentRegion(BufferModificationAction):
    name = _("&Comment Region")
    tooltip = _("Comment a line or region")
    icon = 'icons/text_indent_rob.png'
    key_bindings = {'emacs': 'C-C C-C',}

    def modify(self, mode, pos=-1):
        if hasattr(mode, 'comment') and mode.comment is not None:
            mode.comment(True)


class StandardReturnMixin(debugmixin):
    def findIndent(self, linenum):
        """Find proper indention of next line given a line number.

        This is designed to be overridden in subclasses.  Given the
        current line, figure out what the indention should be for the
        next line.
        """
        return self.stc.GetLineIndentation(linenum)
        
    def electricReturn(self):
        """Add a newline and indent to the proper tab level.

        Indent to the level of the line above.
        """
        s = self.stc
        linesep = s.getLinesep()

        # reindent current line (if necessary), then process the return
        pos = self.reindent()
        
        linenum = s.GetCurrentLine()
        #pos = s.GetCurrentPos()
        col = s.GetColumn(pos)
        linestart = s.PositionFromLine(linenum)
        line = s.GetLine(linenum)[:pos-linestart]
    
        #get info about the current line's indentation
        ind = s.GetLineIndentation(linenum)

        dprint("format = %s col=%d ind = %d" % (repr(linesep), col, ind)) 

        s.SetTargetStart(pos)
        s.SetTargetEnd(pos)
        if col <= ind:
            newline = linesep+s.GetIndentString(col)
        elif not pos:
            newline = linesep
        else:
            ind = self.findIndent(linenum)
            newline = linesep+s.GetIndentString(ind)
        s.ReplaceTarget(newline)
        s.GotoPos(pos + len(newline))

class ElectricReturn(BufferModificationAction):
    name = _("Electric Return")
    tooltip = _("Indent the next line following a return")
    icon = 'icons/text_indent_rob.png'
    key_bindings = {'default': 'RET',}

    def modify(self, mode, pos=-1):
        mode.electricReturn()


class ReindentBase(debugmixin):
    def reindent(self, linenum=None):
        """Reindent the specified line to the correct level.

        Given a line, indent to the previous line
        """
        s = self.stc
        if linenum is None:
            linenum = s.GetCurrentLine()
        if linenum == 0:
            # first line is always indented correctly
            return s.GetCurrentPos()
        
        linestart = s.PositionFromLine(linenum)

        # actual indention of current line
        indcol = s.GetLineIndentation(linenum) # columns
        pos = s.GetCurrentPos()
        indpos = s.GetLineIndentPosition(linenum) # absolute character position
        col = s.GetColumn(pos)
        dprint("linestart=%d pos=%d indpos=%d col=%d indcol=%d" % (linestart, pos, indpos, col, indcol))

        indstr = self.getReindentString(linenum, linestart, pos, indpos, col, indcol)
        if indstr is None:
            return pos
        
        # the target to be replaced is the leading indention of the
        # current line
        s.SetTargetStart(linestart)
        s.SetTargetEnd(indpos)
        s.ReplaceTarget(indstr)

        # recalculate cursor position, because it may have moved if it
        # was within the target
        after = s.GetLineIndentPosition(linenum)
        dprint("after: indent=%d cursor=%d" % (after, s.GetCurrentPos()))
        if pos < linestart:
            return pos
        newpos = pos - indpos + after
        if newpos < linestart:
            # we were in the indent region, but the region was made smaller
            return after
        elif pos < indpos:
            # in the indent region
            return after
        return newpos

    def getReindentString(self, linenum, linestart, pos, indpos, col, indcol):
        return None


class StandardReindentMixin(ReindentBase):
    def getReindentString(self, linenum, linestart, pos, indpos, col, indcol):
        s = self.stc
        
        # look at indention of previous line
        prevind, prevline = s.GetPrevLineIndentation(linenum)
        if (prevind < indcol and prevline < linenum-1) or prevline < linenum-2:
            # if there's blank lines before this and the previous
            # non-blank line is indented less than this one, ignore
            # it.  Make the user manually unindent lines.
            return None

        # previous line is not blank, so indent line to previous
        # line's level
        return s.GetIndentString(prevind)


class FoldingReindentMixin(debugmixin):
    def reindent(self, linenum=None):
        """Reindent the specified line to the correct level.

        Given a line, use Scintilla's built-in folding to determine
        the indention level of the current line.
        """
        s = self.stc
        if linenum is None:
            linenum = s.GetCurrentLine()
        linestart = s.PositionFromLine(linenum)

        # actual indention of current line
        ind = s.GetLineIndentation(linenum) # columns
        pos = s.GetLineIndentPosition(linenum) # absolute character position

        # folding says this should be the current indention
        fold = s.GetFoldLevel(linenum)&wx.stc.STC_FOLDLEVELNUMBERMASK - wx.stc.STC_FOLDLEVELBASE
        dprint("ind = %s (char num=%d), fold = %s" % (ind, pos, fold))
        s.SetTargetStart(linestart)
        s.SetTargetEnd(pos)
        s.ReplaceTarget(s.GetIndentString(fold))


class Reindent(BufferModificationAction):
    name = _("Reindent")
    tooltip = _("Reindent a line or region")
    icon = 'icons/text_indent_rob.png'
    key_bindings = {'default': 'C-TAB',}

    def modify(self, mode, pos=-1):
        s = mode.stc

        # save cursor information so the cursor can be maintained at
        # the same relative location in the text after the indention
        pos = mode.reindent()
        s.GotoPos(pos)


class PasteAtColumn(Paste):
    name = _("Paste at Column")
    tooltip = _("Paste selection indented to the cursor's column")
    icon = "icons/paste_plain.png"

    def action(self, pos=-1):
        mode = self.frame.getActiveMajorMode()
        if mode:
            mode.stc.PasteAtColumn()


class EOLModeSelect(BufferBusyActionMixin, RadioAction):
    name="Line Endings"
    inline=False
    tooltip="Switch line endings"

    items = ['Unix (LF)', 'DOS/Windows (CRLF)', 'Old-style Apple (CR)']
    modes = [wx.stc.STC_EOL_LF, wx.stc.STC_EOL_CRLF, wx.stc.STC_EOL_CR]

    def saveIndex(self,index):
        assert self.dprint("index=%d" % index)

    def getIndex(self):
        mode = self.frame.getActiveMajorMode()
        eol = mode.stc.GetEOLMode()
        return EOLModeSelect.modes.index(eol)
                                           
    def getItems(self):
        return EOLModeSelect.items

    def action(self, index=0, old=-1):
        mode = self.frame.getActiveMajorMode()
        mode.stc.ConvertEOLs(EOLModeSelect.modes[index])
        Publisher().sendMessage('resetStatusBar')


class FundamentalMode(MajorMode, BraceHighlightMixin,
                      StandardCommentMixin, StandardReturnMixin,
                      StandardReindentMixin):
    """
    The base view of most (if not all) of the views that use the STC
    to directly edit the text.  Views (like the HexEdit view or an
    image viewer) that only use the STC as the backend storage are
    probably not based on this view.
    """
    keyword='Fundamental'
    regex=".*"

    start_line_comment = ''
    end_line_comment = ''

    # increment after every style change
    style_number = 0

    default_settings = {
        'tab_size': 4,
        'tab_style': 'mixed',
        'line_numbers': True,
        'line_number_margin_width': 40,
        'symbols': False,
        'symbols_margin_width': 16,
        'folding': False,
        'folding_margin_width': 16,
        'word_wrap': False,
        'backspace_unindents': True,
        'indentation_guides': True,
        'highlight_column': 30,
        'edge_column': 80,
        'edge_indicator': 'line',
        'caret_blink_rate': 0,
        'caret_width': 2,
        'caret_line_highlight': False,
        'sample_file': "Fundamental mode is the base for all other modes that use the STC to view text.",
        'has_stc_styling': True,
        'stc_lexer': wx.stc.STC_LEX_NULL,
        'stc_keywords': "",
        'stc_boa_braces': "{}",
        'stc_boa_style_names': {},
        'stc_lexer_styles': {},

        # Note: 1 tends to be the comment style, but not in all cases.
        'stc_lexer_default_styles': {0: '',
                                     1: 'fore:%(comment-col)s,italic',
                                     wx.stc.STC_STYLE_DEFAULT: 'face:%(mono)s,size:%(size)d',
                                     wx.stc.STC_STYLE_LINENUMBER: 'face:%(ln-font)s,size:%(ln-size)d',
                                     
                                     wx.stc.STC_STYLE_BRACEBAD: '',
                                     wx.stc.STC_STYLE_BRACELIGHT: '',
                                     wx.stc.STC_STYLE_CONTROLCHAR: '',
                                     wx.stc.STC_STYLE_INDENTGUIDE: '',
                                     }
        }
    
    def createEditWindow(self,parent):
        assert self.dprint("creating new Fundamental window")
        self.createSTC(parent)
        win=self.stc
        return win

    def createSTC(self,parent):
        """Create the STC and apply styling settings.

        Everything that subclasses from FundamentalMode will use an
        STC instance for displaying the user interaction window.
        
        Styling information is loaded from the stc-styles.rc.cfg files
        that the boa styling editor uses.  This file is located in the
        default configuration directory of the application on a
        per-user basis, and in the peppy/config directory on a
        site-wide basis.
        """
        self.stc=PeppySTC(parent,refstc=self.buffer.stc)
        self.current_style = self.__class__.style_number

        self.applyDefaultSettings()
        if self.styleSTC():
            self.settings.has_stc_styling = True
        else:
            # If the style file fails to load, it probably means that
            # the style definition doesn't exist in the style file.
            # So, add the default style settings supplied by the major
            # mode to the file and try again.
            self.styleDefault()
            if self.styleSTC():
                self.settings.has_stc_styling = True
            else:
                # If the file still doesn't load, fall back to a style
                # that hopefully does exist.  The boa stc styling
                # dialog won't be available.
                self.settings.has_stc_styling = False
                self.styleSTC('text')

    def createStatusIcons(self):
        linesep = self.stc.getLinesep()
        if linesep == '\r\n':
            self.statusbar.addIcon("icons/windows.png", "DOS/Windows line endings")
        elif linesep == '\r':
            self.statusbar.addIcon("icons/apple.png", "Old-style Apple line endings")
        else:
            self.statusbar.addIcon("icons/tux.png", "Unix line endings")

    def styleDefault(self):
        """Create entry in stc configuration file for this mode.

        If the style definitions don't exist in the stc configuration
        file, use the defaults supplied by the major mode to add them
        to the file.

        FIXME: The format itself is a bit fragile and will cause
        exceptions if a keyword is missing.  Need to have a robust way
        of handling errors in a user-edited style file.

        See the L{peppy.boa.STCStyleEditor} documentation for more
        information on the format of the configuration file.
        """
        if not self.settings.stc_lexer:
            dprint("no STC styling information for major mode %s" % self.keyword)
            return
        boa.updateConfigFile(self.frame.app, self)

    def applyDefaultSettings(self):
        # turn off symbol margin
        if self.settings.symbols:
            self.stc.SetMarginWidth(1, self.settings.symbols_margin_width)
        else:
            self.stc.SetMarginWidth(1, 0)

        # turn off folding margin
        if self.settings.folding:
            self.stc.SetMarginWidth(2, self.settings.folding_margin_width)
        else:
            self.stc.SetMarginWidth(2, 0)

        self.stc.SetProperty("fold", "1")
        self.stc.SetBackSpaceUnIndents(self.settings.backspace_unindents)
        self.stc.SetIndentationGuides(self.settings.indentation_guides)
        self.stc.SetHighlightGuide(self.settings.highlight_column)

        self.setWordWrap()
        self.setLineNumbers()
        self.setFolding()
        self.setTabStyle()
        self.setEdgeStyle()
        self.setCaretStyle()

    def setWordWrap(self,enable=None):
        if enable is not None:
            self.settings.word_wrap=enable
        if self.settings.word_wrap:
            self.stc.SetWrapMode(wx.stc.STC_WRAP_CHAR)
            self.stc.SetWrapVisualFlags(wx.stc.STC_WRAPVISUALFLAG_END)
        else:
            self.stc.SetWrapMode(wx.stc.STC_WRAP_NONE)

    def setLineNumbers(self,enable=None):
        if enable is not None:
            self.settings.line_numbers=enable
        if self.settings.line_numbers:
            self.stc.SetMarginType(0, wx.stc.STC_MARGIN_NUMBER)
            self.stc.SetMarginWidth(0,  self.settings.line_number_margin_width)
        else:
            self.stc.SetMarginWidth(0,0)

    def setFolding(self,enable=None):
        if enable is not None:
            self.settings.folding=enable
        if self.settings.folding:
            self.stc.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
            self.stc.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
            self.stc.SetMarginSensitive(2, True)
            self.stc.SetMarginWidth(2, self.settings.folding_margin_width)
            # Marker definitions from PyPE
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,  "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,  "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,    "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,  "white", "black")
            self.stc.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS, "white", "black")
            self.stc.Bind(wx.stc.EVT_STC_MARGINCLICK, self.onMarginClick)
        else:
            self.stc.SetMarginWidth(2, 0)
            self.stc.Unbind(wx.stc.EVT_STC_MARGINCLICK)

    def setTabStyle(self):
        self.stc.SetIndent(self.settings.tab_size)
        styles = ['ignore', 'consistent', 'mixed', 'tabs', 'spaces']
        if self.settings.tab_style in styles:
            i = styles.index(self.settings.tab_style)
            self.stc.SetProperty('tab.timmy.whinge.level', str(i))
            if i==4:
                self.stc.SetUseTabs(False)
            else:
                self.stc.SetUseTabs(True)

    def setEdgeStyle(self):
        if self.settings.edge_column > 0:
            self.stc.SetEdgeColumn(self.settings.edge_column)
            if self.settings.edge_indicator == 'line':
                self.stc.SetEdgeMode(wx.stc.STC_EDGE_LINE)
            else:
                self.stc.SetEdgeMode(wx.stc.STC_EDGE_BACKGROUND)
        else:
            self.stc.SetEdgeColumn(0)
            self.stc.SetEdgeMode(wx.stc.STC_EDGE_NONE)

    def setCaretStyle(self):
        self.stc.SetCaretPeriod(self.settings.caret_blink_rate)
        self.stc.SetCaretLineVisible(self.settings.caret_line_highlight)
        self.stc.SetCaretWidth(self.settings.caret_width)

    def onMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.stc.FoldAll()
            else:
                lineClicked = self.stc.LineFromPosition(evt.GetPosition())
                if self.stc.GetFoldLevel(lineClicked) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.stc.SetFoldExpanded(lineClicked, True)
                        self.stc.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.stc.GetFoldExpanded(lineClicked):
                            self.stc.SetFoldExpanded(lineClicked, False)
                            self.stc.Expand(lineClicked, False, True, 0)
                        else:
                            self.stc.SetFoldExpanded(lineClicked, True)
                            self.stc.Expand(lineClicked, True, True, 100)
                    else:
                        self.stc.ToggleFold(lineClicked)

    def styleSTC(self, lang=None):
        """Style the STC using the information in the styling config file.

        Call the boa method of styling the stc that reads the styling
        information (including the lexer type) out of its format
        config file.

        @param lang: language keyword to look up in the file
        """
        self.current_style = self.__class__.style_number

        config=boa.getUserConfigFile(self.frame.app)
        if lang is None:
            lang = self.keyword
            
        try:
            boa.initSTC(self.stc, config, lang)
        except SyntaxError:
            dprint("no STC style defined for %s" % lang)
            return False
        return True

    def changeStyle(self):
        """Change the style of this mode and all others like it"""

        self.__class__.style_number += 1
        self.styleSTC()

    def focusPostHook(self):
        if self.current_style != self.__class__.style_number:
            self.styleSTC()

    def OnUpdateUIHook(self, evt):
        self.braceHighlight()

    def commentLine(self, start, end):
        """Add comment to the line specified by start and end.

        Generic method that uses the start_line_comment and
        end_line_comment class attributes to comment a line.  This is
        to be called within a loop that adds comment characters to the
        line.  start and end are assumed to be the endpoints of the
        current line, so no further checking of the line is necessary.

        @param start: first character in line
        @param end: last character in line before line ending

        @returns: new position of last character before line ending
        """
        assert self.dprint("commenting %d - %d: '%s'" % (start, end, self.stc.GetTextRange(start,end)))
        slen = len(self.start_line_comment)
        self.stc.InsertText(start, self.start_line_comment)
        end += slen

        elen = len(self.end_line_comment)
        if elen > 0:
            self.stc.InsertText(end, self.start_line_comment)
            end += elen
        return end + len(self.stc.getLinesep())



class FundamentalPlugin(MajorModeMatcherBase,debugmixin):
    implements(IMajorModeMatcher)
    implements(IMenuItemProvider)
    implements(IToolBarItemProvider)
    implements(IKeyboardItemProvider)
    
    def scanMagic(self,buffer):
        """
        If the buffer looks like it is a text file, flag it as a
        potential Fundamental.
        """
        if not buffer.guessBinary:
            return MajorModeMatch(FundamentalMode,generic=True)
        return None

    default_menu=((None,None,Menu("Test").after("Minor Mode")),
                  (None,"Test",MenuItem(OpenFundamental).first()),
                  ("Fundamental","Edit",MenuItem(PasteAtColumn).after("Paste").before("paste")),
                  ("Fundamental","Edit",MenuItem(FindText)),
                  ("Fundamental","Edit",MenuItem(ReplaceText)),
                  ("Fundamental","Edit",MenuItem(GotoLine)),
                  ("Fundamental","Format",MenuItem(EOLModeSelect)),
                  ("Fundamental","Format",Separator()),
                  ("Fundamental","View",MenuItem(WordWrap)),
                  ("Fundamental","View",MenuItem(LineNumbers)),
                  ("Fundamental","View",MenuItem(Folding)),
                  ("Fundamental","View",Separator("cmdsep")),
                  ("Fundamental",None,Menu("Cmds").after("Edit")),
                  ("Fundamental","Cmds",MenuItem(ShiftLeft)),
                  ("Fundamental","Cmds",MenuItem(ShiftRight)),
                  ("Fundamental","Cmds",MenuItem(Reindent)),
                  ("Fundamental","Cmds",Separator("shift").last()),
                  ("Fundamental","Cmds",MenuItem(CommentRegion)),
                  )
    def getMenuItems(self):
        for mode,menu,item in self.default_menu:
            yield (mode,menu,item)

    default_tools=(("Fundamental",None,Menu("Cmds").after("Major Mode")),
                   ("Fundamental","Cmds",MenuItem(ShiftLeft)),
                   ("Fundamental","Cmds",MenuItem(ShiftRight)),
                   )
    def getToolBarItems(self):
        for mode,menu,item in self.default_tools:
            yield (mode,menu,item)

    default_keys=(("Fundamental",BeginningTextOfLine),
                  ("Fundamental",EndOfLine),
                  ("Fundamental",PreviousLine),
                  ("Fundamental",NextLine),
                  ("Fundamental",CapitalizeWord),
                  ("Fundamental",UpcaseWord),
                  ("Fundamental",DowncaseWord),
                  ("Fundamental",ElectricReturn),
                  )
    def getKeyboardItems(self):
        for mode,action in self.default_keys:
            yield (mode,action)


if __name__ == "__main__":
    app=testapp(0)
    frame=RootFrame(app.main)
    frame.Show(True)
    app.MainLoop()

