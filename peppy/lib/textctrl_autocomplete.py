"""
wxPython Custom Widget Collection 20060207
Written By: Edward Flick (eddy -=at=- cdf-imaging -=dot=- com)
            Michele Petrazzo (michele -=dot=- petrazzo -=at=- unipex -=dot=- it)
            Will Sadkin (wsadkin-=at=- nameconnector -=dot=- com)
Copyright 2006 (c) CDF Inc. ( http://www.cdf-imaging.com )
Contributed to the wxPython project under the wxPython project\'s license.
"""
import locale, wx, sys, cStringIO


class FakePopupWindow(wx.MiniFrame):
    def __init__(self, parent, style=None):
        wx.MiniFrame.__init__(self, parent, style = wx.NO_BORDER
                              | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP)
        self.Panel = wx.Panel(self)
        self.list = None

    def setList(self, list):
        #self.GetSizer().Add(list, 1, wx.EXPAND)
        #self.SetAutoLayout(True)
        #list.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        #list.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.list = list

    def Position(self, position, size):
        #print("pos=%s size=%s" % (position, size))
        self.Move((position[0]+size[0], position[1]+size[1]))
        
    def SetPosition(self, position):
        #print("pos=%s" % (position))
        self.Move((position[0], position[1]))
        
    def SetBackgroundColour(self, colour):
        self.Panel.SetBackgroundColour(colour)
    
    def Window(self):
        return self.Panel
    
    def ActivateParent(self):
        """Activate the parent window
        @postcondition: parent window is raised

        """
        parent = self.GetParent()
        parent.Raise()
        parent.SetFocus()

    def OnFocus(self, evt):
        """Raise and reset the focus to the parent window whenever
        we get focus.
        @param evt: event that called this handler

        """
        print("On Focus: set focus to %s" % str(self.GetParent()))
        self.ActivateParent()
        self.list.SetFocus()
        evt.Skip()

    Window = property(Window)
    
if wx.Platform == '__WXMAC__':
    wx.PopupWindow = FakePopupWindow


class FakePopup(wx.Frame):
    def __init__(self, parent, pos=wx.DefaultPosition):
        style = wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT
        if wx.Platform == '__WXMAC__':
            style = style | wx.BORDER_NONE | wx.POPUP_WINDOW
        else:
            style = style | wx.SIMPLE_BORDER
        wx.Frame.__init__(self, parent, pos=pos, style=style)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)
        
        self.list = None
    
    def OnKillFocus(self, evt):
        win = evt.GetEventObject()
        print("list losing focus %s" % win)
        evt.Skip()

    def setKillFocus(self, callback):
        self.GetParent().Bind(wx.EVT_KILL_FOCUS, callback, self.GetParent())
        self.list.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        pass
    
    def setList(self, list):
        self.GetSizer().Add(list, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        list.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        list.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.list = list
    
    def Show(self, state=True):
        print("Showing %s" % state)
        import traceback
        traceback.print_stack()
        if state:
            wx.Frame.Show(self, state)
        else:
            wx.Frame.Show(self, state)

    def ActivateParent(self):
        """Activate the parent window
        @postcondition: parent window is raised

        """
        parent = self.GetParent()
        parent.Raise()
        parent.SetFocus()

    def OnFocus(self, evt):
        """Raise and reset the focus to the parent window whenever
        we get focus.
        @param evt: event that called this handler

        """
        print("On Focus: set focus to %s" % str(self.GetParent()))
        self.ActivateParent()
        self.GetParent().SetFocus()
        evt.Skip()

    def OnKeyUp(self, evt):
        """Process key upevents in the control
        @param evt: event that called this handler

        """
        if evt.GetKeyCode() == wx.WXK_RETURN:
            self.__PostEvent()
        else:
            evt.Skip()


class HighlightListBox(wx.HtmlListBox):
    """Virtual List Box used to highlight partial matches in the ListCtrl"""
    def setChoices(self, choices):
        self.choices = choices
        self.clearBold()
        self.SetItemCount(len(choices))
        
    def setBold(self, index, start, count):
        self.bold[index] = (start, start+count)
        #print(self.bold[index])
        self.RefreshLine(index)
        
    def clearBold(self):
        self.bold = [None] * len(self.choices)
        if len(self.choices) > 0:
            self.RefreshLines(0, len(self.choices) - 1)
        
    def OnGetItem(self, n):
        if hasattr(self, 'bold') and self.bold[n] is not None:
            text = self.choices[n]
            start = self.bold[n][0]
            end = self.bold[n][1]
            val = "%s<b>%s</b>%s" % (text[0:start], text[start:end], text[end:])
            #print "index %d: %s" % (n, val)
            return val
        return self.choices[n]
    
    def selectNextMatch(self):
        """Set the selection to the next match in the list.
        
        A match is determined by any item that exists in the bold list.  The
        selection will wrap around to the top of the list.
        """
        start = self.GetSelection()
        index = start + 1
        count = self.GetLineCount()
        while index < count:
            if self.bold[index] is not None:
                break
            index += 1
        if index >= count:
            index = 0
            while index < start:
                if self.bold[index] is not None:
                    break
                index += 1
            if index == start and self.bold[index] is None:
                index += 1
                if index >= count:
                    index = 0
        if index < count:
            self.SetSelection(index)
    
    def selectPrevMatch(self):
        """Set the selection to the previous match in the list.
        
        A match is determined by any item that exists in the bold list.  The
        selection will wrap around to the bottom of the list.
        """
        start = self.GetSelection()
        index = start - 1
        count = self.GetLineCount()
        while index >= 0:
            if self.bold[index] is not None:
                break
            index -= 1
        if index < 0:
            index = count - 1
            while index > start:
                if self.bold[index] is not None:
                    break
                index -= 1
            if index == start and self.bold[index] is None:
                index -= 1
                if index < 0:
                    index = count - 1
        if index >= 0:
            self.SetSelection(index)

    def getLargestCommon(self, input):
        """Get the largest common string from the list of already matched strings.
        
        Using the list of strings that already have been matched, see if there
        are any more characters that can be matched that are in common among
        all of the strings.
        """
        found = None
        start = len(input)
        most = None
        for index, bold in enumerate(self.bold):
            if bold is not None:
                text = self.choices[index][bold[0]:]
                if found is None:
                    # get first match
                    found = text
                    most = len(found)
                else:
                    for j in range(start, most):
                        if text[j] != found[j]:
                            most = j
                            break
                #print "after %d %s: found=%s most=%d" % (index, text, found, most)
        if not found:
            found = input
        else:
            found = found[0:most]
        return found


class TextCtrlAutoComplete(wx.TextCtrl):
    def __init__ (self, parent, choices=None, dropDownClick=True,
                  hideOnNoMatch=True, entryCallback=None, matchFunction=None,
                   mac=False,
                  **therest) :
        """
        Constructor works just like wx.TextCtrl except you can pass in a
        list of choices.  You can also change the choice list at any time
        by calling setChoices.
        """
        if therest.has_key('style'):
            therest['style']=wx.TE_PROCESS_ENTER | therest['style']
        else:
            therest['style']=wx.TE_PROCESS_ENTER
        wx.TextCtrl.__init__(self, parent, **therest )
        #Some variables
        self._dropDownClick = dropDownClick
        self._choices = choices
        self._lastinsertionpoint = 0
        self._hideOnNoMatch = hideOnNoMatch
        self._entryCallback = entryCallback
        self._matchFunction = matchFunction
        self._screenheight = wx.SystemSettings.GetMetric( wx.SYS_SCREEN_Y )
        self._tabCount = 0
        self._onlyAtStart = False

        self._mac = mac | bool(wx.Platform == '__WXMAC__')
        if self._mac:
            self.dropdown = FakePopupWindow(self)
        else:
            self.dropdown = wx.PopupWindow( self )

        self.dropdownlistbox = HighlightListBox(self.dropdown)
        if mac:
            self.dropdown.setList(self.dropdownlistbox)
            #self.dropdown.setKillFocus(self.onControlChanged)
            #self.Bind( wx.EVT_KILL_FOCUS, self.onControlChanged, self )
        else:
            self.Bind( wx.EVT_KILL_FOCUS, self.onControlChanged, self )
        
        self.SetChoices(choices)

        self.Bind( wx.EVT_TEXT , self.onEnteredText, self )
        self.Bind( wx.EVT_KEY_DOWN , self.onKeyDown, self )
        #If need drop down on left click
        if dropDownClick:
            self.Bind ( wx.EVT_LEFT_DOWN , self.onClickToggleDown, self )
            self.Bind ( wx.EVT_LEFT_UP , self.onClickToggleUp, self )
        self.dropdown.Bind( wx.EVT_LISTBOX , self.onListItemSelected, self.dropdownlistbox )
        self.dropdownlistbox.Bind(wx.EVT_LEFT_DOWN, self.onListClick)
        self.dropdownlistbox.Bind(wx.EVT_LEFT_DCLICK, self.onListDClick)

    def onListClick(self, evt):
        toSel = self.dropdownlistbox.HitTest( evt.GetPosition() )
        #no values on poition, return
        if toSel == -1: return
        self.dropdownlistbox.SetSelection(toSel)

    def onListDClick(self, evt):
        self._setValueFromSelected()

    def onEnteredText(self, event):
        text = event.GetString()
        if self._entryCallback:
            self._entryCallback()
        self.dropdownlistbox.clearBold()
        if not text:
            # control is empty; hide dropdown if shown:
            if self.dropdown.IsShown():
                self._showDropDown(False)
            event.Skip()
            return
        best = None
        found = False
        nchar = len(text)
        choices = self._choices
        for numCh, choice in enumerate(choices):
            if self._matchFunction:
                index, count = self._matchFunction(text, choice)
                if count > 0:
                    found = True
                    self.dropdownlistbox.setBold(numCh, index, count)
            else:
                if self._onlyAtStart:
                    if choice.lower().startswith(text.lower()):
                        found = True
                        self.dropdownlistbox.setBold(numCh, 0, nchar)
                else:
                    index = choice.lower().find(text.lower())
                    if index >= 0:
                        found = True
                        self.dropdownlistbox.setBold(numCh, index, nchar)
            if found:
                if best is None:
                    best = numCh
        #print("best = %s" % best)
        if best is not None:
            self._showDropDown(True)
            self.dropdownlistbox.SetSelection(best)
            #self.SetFocus()
        else:
            self.dropdownlistbox.SetSelection(-1)
            if self._hideOnNoMatch:
                self._showDropDown(False)
        self._listItemVisible()
        event.Skip ()

    def onKeyDown ( self, event ) :
        """ Do some work when the user press on the keys:
            up and down: move the cursor
            left and right: move the search
        """
        skip = True
        dd = self.dropdownlistbox
        sel = dd.GetSelection()
        visible = self.dropdown.IsShown()
        KC = event.GetKeyCode()
        if KC == wx.WXK_DOWN :
            if sel < (dd.GetItemCount () - 1) :
                dd.SetSelection ( sel+1 )
                self._listItemVisible()
            self._showDropDown ()
            skip = False
        elif KC == wx.WXK_UP :
            if sel > 0 :
                dd.SetSelection ( sel - 1 )
                self._listItemVisible()
            self._showDropDown ()
            skip = False
        elif KC == wx.WXK_PAGEDOWN:
            if sel == -1:
                dd.SetSelection(0)
            else:
                first = dd.GetVisibleBegin()
                last = dd.GetVisibleEnd()
                if not dd.IsVisible(last):
                    last -= 1
                dd.ScrollPages(1)
                dd.SetSelection(last)
        elif KC == wx.WXK_PAGEUP:
            if sel == -1:
                dd.SetSelection(dd.GetLineCount() - 1)
            else:
                first = dd.GetVisibleBegin()
                last = dd.GetVisibleEnd()
                dd.ScrollPages(-1)
                dd.SetSelection(first)
        if KC == wx.WXK_TAB:
            #print self._choices
            if self._choices:
                self._showDropDown ()

                # Find the largest common match in the list of choices
                # and expand to that
                input = self.GetValue()
                text = dd.getLargestCommon(input)
                if text != input:
                    self.SetValue(text)
                    self.SetInsertionPointEnd()
                else:
                    self._tabCount = 1
                self._tabCount += 1
                if self._tabCount > 1:
                    # scroll the list on multiple consecutive tabs
                    if event.GetModifiers() & wx.MOD_SHIFT:
                        dd.selectPrevMatch()
                    else:
                        dd.selectNextMatch()
                        
            skip = False
        else:
            self._tabCount = 0
        if visible :
            if event.GetKeyCode() == wx.WXK_RETURN :
                self._setValueFromSelected()
                #skip = False
            if event.GetKeyCode() == wx.WXK_ESCAPE :
                self._showDropDown( False )
                skip = False
        if skip :
            event.Skip()

    def onListItemSelected (self, event):
        self._setValueFromSelected()
        event.Skip()

    def onClickToggleDown(self, event):
        self._lastinsertionpoint = self.GetInsertionPoint()
        event.Skip ()

    def onClickToggleUp ( self, event ) :
        if ( self.GetInsertionPoint() == self._lastinsertionpoint ) :
            self._showDropDown ( not self.dropdown.IsShown() )
        wx.CallAfter(self.SetFocus)
        event.Skip ()

    def onControlChanged(self, event):
        #print(event)
        changed = event.GetEventObject()
        other = event.GetWindow()
        #print("changed=%s other=%s" % (changed, other))
        if self.dropdown.IsShown():
            self._showDropDown( False )
#            if self._mac:
#                if changed == self:
#                    wx.CallAfter(self.SetFocus)
#                else:
#                    self._showDropDown( False )
#            else:
#                self._showDropDown( False )
        event.Skip()

    def SetChoices(self, choices):
        """
        Sets the choices available in the popup wx.ListBox.
        The items will be sorted case insensitively.
        """
        if not isinstance(choices, list):
            self._choices = [ x for x in choices]
        else:
            self._choices = choices
        self.dropdownlistbox.setChoices(self._choices)
        #prevent errors on "old" systems
        if sys.version.startswith("2.3"):
            self._choices.sort(lambda x, y: cmp(x.lower(), y.lower()))
        else:
            try:
                self._choices.sort(key=lambda x: locale.strxfrm(x).lower())
            except UnicodeEncodeError:
                self._choices.sort(key=lambda x: locale.strxfrm(x.encode("UTF-8")).lower())
        self._setListSize()

    def GetChoices(self):
        return self._choices

    def SetSelectCallback(self, cb=None):
        self._selectCallback = cb

    def SetEntryCallback(self, cb=None):
        self._entryCallback = cb

    def SetMatchFunction(self, mf=None):
        self._matchFunction = mf

    #-- Internal methods
    def _setValueFromSelected( self ) :
        """
        Sets the wx.TextCtrl value from the selected wx.ListCtrl item.
        Will do nothing if no item is selected in the wx.ListCtrl.
        """
        sel = self.dropdownlistbox.GetSelection()
        if sel > -1:
            itemtext = self._choices[sel]
            self.SetValue (itemtext)
            self.SetInsertionPointEnd ()
            self.SetSelection(-1, -1)
            self._showDropDown ( False )

    def _showDropDown ( self, show = True ) :
        """
        Either display the drop down list (show = True) or hide it (show = False).
        """
        if show :
            size = self.dropdown.GetSize()
            width, height = self . GetSizeTuple()
            x, y = self . ClientToScreenXY ( 0, height )
            if size.GetWidth() != width :
                size.SetWidth(width)
                self.dropdown.SetSize(size)
                self.dropdownlistbox.SetSize(self.dropdown.GetClientSize())
            if (y + size.GetHeight()) < self._screenheight :
                self.dropdown . SetPosition ( wx.Point(x, y) )
            else:
                self.dropdown . SetPosition ( wx.Point(x, y - height - size.GetHeight()) )
        self.dropdown.Show ( show )

    def _listItemVisible( self ) :
        """
        Moves the selected item to the top of the list ensuring it is always visible.
        """
        toSel =  self.dropdownlistbox.GetSelection ()
        if toSel == -1: return
        self.dropdownlistbox.SetSelection( toSel )

    def _setListSize(self):
        choices = self._choices
        longest = 0
        for choice in choices :
            longest = max(len(choice), longest)
        longest += 3
        itemcount = min( len( choices ) , 7 ) + 2
        charheight = self.dropdownlistbox.GetCharHeight()
        charwidth = self.dropdownlistbox.GetCharWidth()
        self.popupsize = wx.Size( charwidth*longest, charheight*itemcount )
        self.dropdownlistbox.SetSize ( self.popupsize )
        self.dropdown.SetClientSize( self.popupsize )

class test:
    def __init__(self):
        args = dict()
        if 1:
            args["colNames"] = ("col1", "col2")
            args["multiChoices"] = [ ("Zoey","WOW"), ("Alpha", "wxPython"),
                                    ("Ceda","Is"), ("Beta", "fantastic"),
                                    ("zoebob", "!!")]
            args["colFetch"] = 1
        else:
            args["choices"] = ["123", "cs", "cds", "Bob","Marley","Alpha"]
        args["selectCallback"] = self.selectCallback
        self.dynamic_choices = [
                        'aardvark', 'abandon', 'acorn', 'acute', 'adore',
                        'aegis', 'ascertain', 'asteroid',
                        'beautiful', 'bold', 'classic',
                        'daring', 'dazzling', 'debonair', 'definitive',
                        'effective', 'elegant',
                        'http://python.org', 'http://www.google.com',
                        'fabulous', 'fantastic', 'friendly', 'forgiving', 'feature',
                        'sage', 'scarlet', 'scenic', 'seaside', 'showpiece', 'spiffy',
                        'www.wxPython.org', 'www.osafoundation.org'
                        ]
        app = wx.PySimpleApp()
        frm = wx.Frame(None,-1,"Test",style=wx.TAB_TRAVERSAL|wx.DEFAULT_FRAME_STYLE)
        panel = wx.Panel(frm)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._ctrl = TextCtrlAutoComplete(panel, **args)
        but = wx.Button(panel,label="Set other multi-choice")
        but.Bind(wx.EVT_BUTTON, self.onBtMultiChoice)
        but2 = wx.Button(panel,label="Set other one-colum choice")
        but2.Bind(wx.EVT_BUTTON, self.onBtChangeChoice)
        but3 = wx.Button(panel,label="Set the starting choices")
        but3.Bind(wx.EVT_BUTTON, self.onBtStartChoices)
        but4 = wx.Button(panel,label="Enable dynamic choices")
        but4.Bind(wx.EVT_BUTTON, self.onBtDynamicChoices)
        sizer.Add(but, 0, wx.ADJUST_MINSIZE, 0)
        sizer.Add(but2, 0, wx.ADJUST_MINSIZE, 0)
        sizer.Add(but3, 0, wx.ADJUST_MINSIZE, 0)
        sizer.Add(but4, 0, wx.ADJUST_MINSIZE, 0)
        sizer.Add(self._ctrl, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        panel.SetAutoLayout(True)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        sizer.SetSizeHints(panel)
        panel.Layout()
        app.SetTopWindow(frm)
        frm.Show()
        but.SetFocus()
        app.MainLoop()

    def onBtChangeChoice(self, event):
        #change the choices
        self._ctrl.SetChoices(["123", "cs", "cds", "Bob","Marley","Alpha"])
        self._ctrl.SetEntryCallback(None)
        self._ctrl.SetMatchFunction(None)

    def onBtMultiChoice(self, event):
        #change the choices
        self._ctrl.SetMultipleChoices( [ ("Test","Hello"), ("Other word","World"),
                                        ("Yes!","it work?") ], colFetch = 1 )
        self._ctrl.SetEntryCallback(None)
        self._ctrl.SetMatchFunction(None)

    def onBtStartChoices(self, event):
        #change the choices
        self._ctrl.SetMultipleChoices( [ ("Zoey","WOW"), ("Alpha", "wxPython"),
                                    ("Ceda","Is"), ("Beta", "fantastic"),
                                    ("zoebob", "!!")], colFetch = 1 )
        self._ctrl.SetEntryCallback(None)
        self._ctrl.SetMatchFunction(None)

    def onBtDynamicChoices(self, event):
        """
        Demonstrate dynamic adjustment of the auto-complete list, based on what's
        been typed so far:
        """
        self._ctrl.SetChoices(self.dynamic_choices)
        self._ctrl.SetEntryCallback(self.setDynamicChoices)
        self._ctrl.SetMatchFunction(self.match)

    def match(self, text, choice):
        """
        Demonstrate "smart" matching feature, by ignoring http:// and www. when doing
        matches.
        """
        t = text.lower()
        c = choice.lower()
        if c.startswith(t): return True
        if c.startswith(r'http://'): c = c[7:]
        if c.startswith(t): return True
        if c.startswith('www.'): c = c[4:]
        if c.startswith(t):
            return 0, len(t)
        return -1, 0

    def setDynamicChoices(self):
        ctrl = self._ctrl
        text = ctrl.GetValue().lower()
        current_choices = ctrl.GetChoices()
        choices = [choice for choice in self.dynamic_choices if self.match(text, choice)]
        if choices != current_choices:
            ctrl.SetChoices(choices)

    def selectCallback(self, values):
        """ Simply function that receive the row values when the
            user select an item
        """
        print "Select Callback called...:",  values

if __name__ == "__main__":
    dynamic_choices = [
                    'aardvark', 'abandon', 'acorn', 'acute', 'adore',
                    'aegis', 'ascertain', 'asteroid',
                    'beautiful', 'bold', 'classic',
                    'daring', 'daft', 'debonair', 'definitive', 'defective',
                    'effective', 'elegant',
                    'http://python.org', 'http://www.google.com',
                    'fabulous', 'fantastic', 'friendly', 'forgiving', 'feature',
                    'sage', 'scarlet', 'scenic', 'seaside', 'showpiece', 'spiffy',
                    'www.wxPython.org', 'www.osafoundation.org',
                    'zqqqq1', 'zqqqq2222', 'zqqqq2228',
                    ]
    app = wx.PySimpleApp()
    frm = wx.Frame(None,-1,"Test",style=wx.TAB_TRAVERSAL|wx.DEFAULT_FRAME_STYLE)
    panel = wx.Panel(frm)
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    normal = TextCtrlAutoComplete(panel, choices=dynamic_choices)
    sizer.Add(normal, 1)
    mac = TextCtrlAutoComplete(panel, mac=True, choices=dynamic_choices)
    sizer.Add(mac, 1)
    panel.SetAutoLayout(True)
    panel.SetSizer(sizer)
    sizer.Fit(panel)
    sizer.SetSizeHints(panel)
    panel.Layout()
    app.SetTopWindow(frm)
    frm.Show()
    app.MainLoop()
