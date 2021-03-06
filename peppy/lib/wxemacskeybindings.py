#-----------------------------------------------------------------------------
# Name:        wxemacskeybindings.py
# Purpose:     multi-keystroke commands, ala emacs
#
# Author:      Rob McMullen
#
# Created:     2007
# RCS-ID:      $Id: $
# Copyright:   (c) 2007 Rob McMullen
# License:     wxWidgets
#-----------------------------------------------------------------------------
"""Multiple keystrokes for command processing.

This module is based on demo program by Josiah Carlson found at
http://wiki.wxpython.org/index.cgi/Using_Multi-key_Shortcuts that
provides the ability to match an arbitrary sequence of keystrokes to a
single command.
"""

import sys
import wx

# The list of all the wx keynames (without the WXK_ prefix) is needed by both
# KeyMap and KeyProcessor objects
wxkeynames = [i[4:] for i in dir(wx) if i.startswith('WXK_')]

# Mapping of wx keystroke numbers to keystroke names
wxkeys = {}
for i in wxkeynames:
    wxkeys[getattr(wx, "WXK_"+i)] = i
for i in ("SHIFT", "ALT", "COMMAND", "CONTROL", "MENU"):
    if wx.Platform == '__WXGTK__':
        # unix doesn't create a keystroke when a modifier key
        # is also modified by another modifier key, so we
        # create entries here so that decode() doesn't have to
        # have platform-specific code
        wxkeys[getattr(wx, "WXK_"+i)] = i[0:1]+'-'
    else:
        wxkeys[getattr(wx, "WXK_"+i)] = ''

# Aliases for WXK_ names
keyaliases={'RET':'RETURN',
            'SPC':'SPACE',
            'ESC':'ESCAPE',
            }

# Emacs style modifiers are used internally to specify which of the modifier
# keys are pressed.  They are used as in "C-x" to mean Control-X.
#
# Prefixes:
#  C-   Control on MSW/GTK; Command on Mac
#  ^-   Control on Mac, aliased to C- on MSW/GTK
#  S-   Shift
#  M-   Alt/Option on MAC; Alt on MSW/GTK
#  A-   aliased to M- on all platforms
emacs_modifiers=['^-', 'C-','S-','A-','M-']

if wx.Platform == '__WXMAC__':
    # WXMAC needs Command to appear as Ctrl- in the accelerator text.  It
    # converts Ctrl into the command symbol.  Note that there is no mapping
    # for the C- prefix because wx doesn't have the ability to put a Control
    # character in a menu.
    modaccelerator = {
        '^-': '^',
        'S-': 'Shift-', # Shift appears in the menu item as an up arrow
        'C-': 'Ctrl-', # Ctrl appears in the menu item as the command cloverleaf
        'M-': 'Alt-', # Alt appears in the menu item as the option character
        }
    modaliases={
        'Command-':'C-',
        'Cmd-':'C-',
        'Command+':'C-',
        'Cmd+':'C-',
        '^':'^-',
        'Ctrl-':'^-',
        'Ctrl+':'^-',
        'Shift-':'S-',
        'Shift+':'S-',
        'Alt-':'M-',
        'Alt+':'M-',
        'Option-':'M-',
        'Option+':'M-',
        'Meta-':'M-',
        'Meta+':'M-',
        }
else:
    modaccelerator = {
        '^-': 'Ctrl-',
        'C-': 'Ctrl-',
        'S-': 'Shift-',
        'A-': 'Alt-',
        'M-': 'Alt-',
        }
    modaliases={
        '^':'C-',
        'Ctrl-':'C-',
        'Shift-':'S-',
        'Alt-':'A-',
        'Meta-':'M-',
        'Ctrl+':'C-',
        'Shift+':'S-',
        'Alt+':'A-',
        'Meta+':'M-',
        }



class DuplicateKeyError(Exception):
    pass


class KeyAccelerator(object):
    debug = False
    
    # Cache that maps accelerator string to the sequence of keystrokes
    cache = {}

    @classmethod
    def split(cls, acc):
        """Split the accelerator string (e.g. "C-X C-S") into
        individual keystrokes, expanding abbreviations and
        standardizing the order of modifier keys.
        """
        try:
            return cls.cache[acc]
        except KeyError:
            if cls.debug: print("accelerator %s not found; creating keystrokes" % acc)
            return cls._splitAccelerator(acc)
    
    @classmethod
    def _splitAccelerator(cls, acc):
        if acc.find('\t')>=0:
            # match the original format from the wxpython wiki, where
            # keystrokes are delimited by tab characters
            keystrokes = [i for i in acc.split('\t') if i]
        else:
            # find the individual keystrokes from a more emacs style
            # list, where the keystrokes are separated by whitespace.
            keystrokes=[]
            i=0
            flags={}
            while i<len(acc):
                while acc[i].isspace() and i<len(acc): i+=1

                # check all modifiers in any order.  C-S-key and
                # S-C-key mean the same thing.
                j=i
                for m in emacs_modifiers: flags[m]=False
                while j<len(acc):
                    chars,m=cls.matchModifier(acc[j:])
                    if m:
                        j+=chars
                        flags[m]=True
                    else:
                        break
                if cls.debug: print "modifiers found: %s.  remaining='%s'" % (str(flags), acc[j:])
                
                chars,key=cls.matchKey(acc[j:])
                if key is not None:
                    if cls.debug: print "key found: %s, chars=%d" % (key, chars)
                    keys="".join([m for m in emacs_modifiers if flags[m]])+key
                    if cls.debug: print "keystroke = %s" % keys
                    keystrokes.append(keys)
                else:
                    if cls.debug: print "unknown key %s" % acc[j:j+chars]
                if j+chars < len(acc):
                    if cls.debug: print "remaining='%s'" % acc[j+chars:]
                i=j+chars
        cls.cache[acc] = keystrokes
        if cls.debug: print "keystrokes: %s" % keystrokes
        return keystrokes

    @classmethod
    def matchModifier(cls, str):
        """Find a modifier in the accelerator string
        """        
        for m in emacs_modifiers:
            if str.startswith(m):
                return len(m),m
        for m in modaliases.keys():
            if str.startswith(m):
                return len(m),modaliases[m]
        return 0,None

    @classmethod
    def matchKey(cls, text):
        """Find a keyname (not modifier name) in the accelerator
        string, matching any special keys or abbreviations of the
        special keys
        """
        text = text.upper()
        key = None
        i = 0
        for name in keyaliases:
            if text.startswith(name):
                val = keyaliases[name]
                if text.startswith(val):
                    return i+len(val), val
                else:
                    return i+len(name), val
        for name in wxkeynames:
            if text.startswith(name):
                return i+len(name), name
        if i<len(text) and not text[i].isspace():
            return i+1, text[i].upper()
        return i, None

    @classmethod
    def nonEmacsName(cls, acc):
        modifiers=[]
        j=0
        try:
            while j<len(acc):
                chars,m=cls.matchPlatformModifier(acc[j:])
                if m:
                    j+=chars
                    modifiers.append(m)
                else:
                    modifiers.append(acc[j:])
                    break
        except TypeError:
            # Type error will result from trying to take the length of None,
            # should a control character be specified on the Mac.  wx doesn't
            # have the ability to put a control character in a Mac menu.
            return ""
        return "".join(modifiers)

    @classmethod
    def matchPlatformModifier(cls, str):
        """Find a modifier in the accelerator string
        """        
        for m in modaccelerator.keys():
            if str.startswith(m):
                return len(m),modaccelerator[m]
        return 0,None

    @classmethod
    def getAcceleratorText(cls, key_sequence, force_emacs=False):
        keystrokes = cls.split(key_sequence)
        if len(keystrokes) == 1 and not force_emacs:
            # if it has a stock id, always force it to use the our
            # accelerator because wxWidgets will put one there anyway and
            # we need to overwrite it with our definition
            acc = KeyAccelerator.nonEmacsName(keystrokes[0])
            if acc:
                text = u"\t%s" % acc
            else:
                text = ""
        else:
            text = u"    %s" % " ".join(keystrokes)
        return text


class KeyMap(object):
    """Group of key mappings.

    This class represents a group of key mappings.  The KeyProcessor
    class below uses multiple groups, one to represent global keymaps,
    one for local keymaps, and an arbitrary number of other keymaps
    for any additional minor modes that need other keymappings.
    """    
    debug = False

    def __init__(self):
        self.lookup={}
        self.reset()
        
        self.function=None

        # if this is true, it will throw an exception when finding a
        # duplicate keystroke.  If false, it silently overwrites any
        # previously defined keystroke with the new one.
        self.exceptionsWhenDuplicate=False
    
    def raiseDuplicateExceptions(self):
        self.exceptionsWhenDuplicate = True

    def reset(self):
        self.cur=self.lookup
        self.function=None

    def add(self, key):
        """
        return True if keystroke is processed by the handler
        """
        if self.cur:
            if key in self.cur:
                # get next item, either a dict of more possible
                # choices or a function to execute
                self.cur=self.cur[key]
                if not isinstance(self.cur, dict):
                    self.function = self.cur
                    self.cur=None
                return True
            elif self.cur is not self.lookup:
                # if we get here, we have processed a partial match,
                # but the most recent keystroke doesn't match
                # anything.  Flag as unknown keystroke combo
                self.cur=None
                return True
            else:
                # OK, this is the first keystroke and it doesn't match
                # any of the first keystrokes in our keymap.  It's
                # probably a regular character, so flag it as
                # unprocessed by our handler.
                self.cur=None
        return False

    def isUnknown(self):
        """Convenience function to check whether the keystroke combo is an
        unknown combo.
        """        
        return self.cur==None and self.function==None

    def findNested(self, hotkeys, actions):
        """Convenience function to find all the actions starting at the given
        spot in the nested dict.
        """
        if not isinstance(hotkeys, dict):
            actions.append(hotkeys)
        else:
            for val in hotkeys.values():
                if isinstance(val, dict):
                    self.findNested(val, actions)
                else:
                    actions.append(val)
    
    def find(self, acc):
        """Find the action(s) associated with the given keystroke combination.
        
        If the keystroke is the prefix of other keystrokes, the list of
        actions that use the given keystrokes as a prefix will be returned.
        
        @return: list of actions
        """
        hotkeys = self.lookup
        if self.debug: print "define: acc=%s" % acc
        keystrokes = KeyAccelerator.split(acc)
        if self.debug: print "define: keystrokes=%s" % str(keystrokes)
        actions = []
        for keystroke in keystrokes:
            if keystroke not in hotkeys:
                # if we didn't find the current keystroke in the current
                # level of the nested dict, we're done because we didn't find
                # a match.
                break
            
            # Go to the next level of the nested dict
            hotkeys = hotkeys[keystroke]
        if isinstance(hotkeys, dict):
            # We've got a dict left, so multiple keystrokes
            self.findNested(hotkeys, actions)
        else:
            actions.append(hotkeys)
        return actions
    
    def createKeybinding(self, key_specifier, action, replace=False):
        """Create keybinding(s) for all key combinations for the given action
        
        """
        if isinstance(key_specifier, list):
            for key in key_specifier:
                self.define(key, action, replace)
        else:
            self.define(key_specifier, action, replace)
    
    def define(self, acc, fcn, replace=False):
        """Create the nested dicts that point to the function to be
        executed on the completion of the keystroke
        """
        hotkeys = self.lookup
        if self.debug: print "define: acc=%s" % acc
        keystrokes = KeyAccelerator.split(acc)
        if self.debug: print "define: keystrokes=%s" % str(keystrokes)
        if keystrokes:
            # create the nested dicts for everything but the last keystroke
            for keystroke in keystrokes[:-1]:
                if keystroke in hotkeys:
                    if self.exceptionsWhenDuplicate and not isinstance(hotkeys[keystroke], dict):
                        raise DuplicateKeyError("Some other hotkey shares a prefix with this hotkey: %s"%acc)
                    if not isinstance(hotkeys[keystroke],dict):
                        # if we're overwriting a function, we need to
                        # replace the function call with a dict so
                        # that the remaining keystrokes can be parsed.
                        hotkeys[keystroke] = {}
                else:
                    hotkeys[keystroke] = {}
                hotkeys = hotkeys[keystroke]

            # the last keystroke maps to the function to execute
            if not replace and self.exceptionsWhenDuplicate and keystrokes[-1] in hotkeys:
                raise DuplicateKeyError("Some other hotkey shares a prefix with this hotkey: %s"%acc)
            hotkeys[keystrokes[-1]] = fcn
        return " ".join(keystrokes)
    
    def processBindings(self, map, lookup, keys):
        for item, action in lookup.iteritems():
            if isinstance(action, dict):
                self.processBindings(map, action, keys + [item])
            else:
                map[action] = tuple(keys + [item])
    
    def getBindings(self):
        """Return a dict that shows the mapping of actions to keystrokes"""
        map = {}
        self.processBindings(map, self.lookup, [])
        return map

class KeyProcessor(object):
    """Driver class for key processing.

    Takes multiple keymaps and looks at them in order, first the minor
    modes, then the local, and finally if nothing matches, the global
    key maps.
    """
    debug = False

    def __init__(self,status=None):
        self.keymaps=[]
        self.minorKeymaps=[]
        self.globalKeymap=KeyMap()
        self.localKeymap=KeyMap()
        self.escapeKeymap = KeyMap()
        
        self.num=0
        self.status=status

        # XEmacs defaults to the Ctrl-G to abort keystroke processing
        self.abortKey="C-G"

        # Probably should create a standard way to process sticky
        # keys, but for now ESC corresponds to a sticky meta key just
        # like XEmacs
        self.useStickyMeta = True
        self.stickyMeta="ESCAPE"
        self.metaNext=False
        self.nextStickyMetaCancel=False
        # Always add the ESC-ESC-ESC quit key sequence
        self.escapeKeymap.define("M-"+self.stickyMeta + " " + self.stickyMeta,
                                 None)

        # Whether or not a CMD or ALT key has been pressed at any point in this
        # keystroke.  Used to determine if the key is printable or not.
        self.modifier = False

        self.number=None
        self.defaultNumber=4 # for some reason, XEmacs defaults to 4
        self.scale=1 # scale factor, usually either 1 or -1
        self.universalArgument="C-U"
        self.processingArgument=0
        
        # If reportNext is not None, instead of being processed the next action
        # is reported to a caller by using reportNext as a callback.
        self.reportNext = None

        # If getNext is not None, instead of being processed the next keystroke
        # is reported to a caller by using getNext as a callback
        self.getNext = None

        self.hasshown=False
        self.reset()

    def findStickyMeta(self):
        """Determine if the sticky meta key should be defined for this set
        of keymaps.
        """
        self.useStickyMeta = False
        sticky = "M-%s" % self.stickyMeta
        for keymap in self.keymaps:
            if sticky in keymap.lookup:
                #print("found M-ESC in keymap = %s" % str(keymap.lookup))
                self.useStickyMeta = True
                break

    def fixmaps(self):
        """set up the search order of keymaps
        """
        self.keymaps=self.minorKeymaps+[self.localKeymap,
                                        self.globalKeymap]
        self.num=len(self.keymaps)
        self.findStickyMeta()
        self.reset()

    def addMinorKeyMap(self,keymap):
        """Add the keymap to the list of keymaps recognized by this
        processor.  Minor mode keymaps are processed in the order that
        they are added.
        """
        self.minorKeymaps.append(keymap)
        self.fixmaps()

    def clearMinorKeyMaps(self):
        self.minorKeymaps=[]
        self.fixmaps()

    def setGlobalKeyMap(self,keymap):
        self.globalKeymap=keymap
        self.fixmaps()

    def clearGlobalKeyMap(self):
        keymap=KeyMap()
        self.setGlobalKeyMap(keymap)

    def setLocalKeyMap(self,keymap):
        self.localKeymap=keymap
        self.fixmaps()

    def clearLocalKeyMap(self):
        keymap=KeyMap()
        self.setLocalKeyMap(keymap)

    def decode(self,evt):
        """Raw event processor that takes the keycode and produces a
        string that describes the key pressed.  The modifier keys are
        always returned in the order C-, S-, A-, M-
        """
        keycode = evt.GetKeyCode()
        raw = evt.GetRawKeyCode()
        keyname = wxkeys.get(keycode, None)
        modifiers = ""
        metadown = False
        emods = evt.GetModifiers()
        
        if wx.Platform == '__WXMAC__':
            # Get the modifier string in order C-, S-, A-, M-
            if emods & wx.MOD_CONTROL:
                modifiers += "^-"
                self.modifier = True
            if emods & wx.MOD_META:
                modifiers += "C-"
                self.modifier = True
            if emods & wx.MOD_SHIFT:
                modifiers += "S-"
            if emods & wx.MOD_ALT:
                modifiers += "M-"
                metadown = True
                self.modifier = True
        else:
            # Get the modifier string in order C-, S-, A-, M-
            if emods & wx.MOD_CMD:
                modifiers += "C-"
                self.modifier = True
            if emods & wx.MOD_SHIFT:
                modifiers += "S-"
            # A- not used currently; meta is called alt
            if emods & wx.MOD_ALT:
                modifiers += "M-"
                metadown = True
                self.modifier = True
        if keycode == wx.WXK_ESCAPE:
            self.modifier = True

        # Check the sticky-meta
        if self.metaNext:
            if not metadown:
                # if the actual meta modifier is not pressed, add it.  We don't want to end up with M-M-key
                modifiers += 'M-'
            self.metaNext=False

            # if this is the second consecutive ESC, flag the next one
            # to cancel the keystroke input
            if keyname==self.stickyMeta:
                self.nextStickyMetaCancel=True
        elif self.useStickyMeta:
            # ESC hasn't been pressed before, so flag it for next
            # time.
            if keyname==self.stickyMeta:
                self.metaNext=True

        # check for printable character
        if keyname is None:
            if 27 < keycode < 256:
                keyname = chr(keycode)
            else:
                keyname = "unknown-%s" % keycode
        if self.debug: print("modifiers: raw=%d processed='%s' keyname=%s keycode=%s key=%s" % (emods, modifiers, keyname, keycode, modifiers+keyname))
        return modifiers + keyname

    def reset(self):
        """reset the lookup table to the root in each keymap.
        """
        if self.debug: print "reset"
        self.sofar = ''
        for keymap in self.keymaps:
            keymap.reset()
        if self.hasshown:
            # If we've displayed some stuff in the status area, clear
            # it.
            self.show('')
            self.hasshown=False
            
        self.modifier = False
        self.number=None
        self.metaNext=False
        self.nextStickyMetaCancel=False
        self.processingArgument=0
        self.args=''

    def show(self,text):
        """Display the current keystroke processing in the status area
        """
        if self.status:
            if self.reportNext:
                text = "Describe Key: %s" % text
            self.status.SetStatusText(text)
            self.hasshown=True

    def add(self, key):
        """Attempt to add this keystroke by processing all keymaps in
        parallel and stop at the first complete match.  The other way
        that processing stops is if the new keystroke is unknown in
        all keymaps.  Returns a tuple (skip,unknown,function), where
        skip is true if the keystroke should be skipped up to the next
        event handler, unknown is true if the partial keymap doesn't
        match anything, and function is either None or the function to
        execute.
        """
        unknown=0
        processed=0
        function=None
        for keymap in self.keymaps:
            if keymap.add(key):
                processed+=1
                if keymap.function:
                    # once the first function is found, we stop processing
                    function=keymap.function
                    break
            if keymap.isUnknown():
                unknown+=1
        if processed>0:
            # at least one keymap is still matching, so continue processing
            self.sofar += key + ' '
            if self.debug: print "add: sofar=%s processed=%d unknown=%d function=%s" % (self.sofar,processed,unknown,function)
        else:
            if unknown==self.num and self.sofar=='':
                # if the keystroke doesn't match the first character
                # in any of the keymaps, don't flag it as unknown.  It
                # is a key that should be processed by the
                # application, not us.
                unknown=0
            if self.debug: print "add: sofar=%s processed=%d unknown=%d skipping %s" % (self.sofar,processed,unknown,key)
        return (processed==0,unknown==self.num,function)

    def startArgument(self, key=None):
        """This starts the emacs-style numeric arguments that are
        ended by the first non-numeric keystroke
        """
        self.number=None
        self.scale=1
        if key is not None:
            self.args=key + ' '
        self.processingArgument=1

    def getNumber(self, key, musthavectrl=False):
        """Helper function to decode a numeric argument keystroke.  It
        can be a number or, if the first keystroke, the '-' sign.  If
        C-U is used to start the argumen processing, the numbers don't
        have to have the Ctrl modifier pressed.
        """
        ctrl=False
        if key[0:2]=='C-':
            key=key[2:]
            ctrl=True
        if musthavectrl and not ctrl:
            return None
        
        # only allow minus sign at first character
        if key=='-' and self.processingArgument==1:
            return -1
        elif key>='0' and key<='9':
            return ord(key)-ord('0')
        return None

    def argument(self, key):
        """Process a numeric keystroke
        """
        # allow control and a number to work as well
        num=self.getNumber(key)
        if num is None:
            # this keystroke isn't a number, so calculate the final
            # value of the numeric argument and flag that we're done
            if self.number is None:
                self.number=self.defaultNumber
            else:
                self.number=self.scale*self.number
            if self.debug: print "number = %d" % self.number
            self.processingArgument=0
        else:
            # this keystroke IS a number, so process it.
            if num==-1:
                self.scale=-1
            else:
                if self.number is None:
                    self.number=num
                else:
                    self.number=10*self.number+num
            self.args+=key + ' '
            self.processingArgument+=1
    
    def setReportNext(self, callback):
        self.reportNext = callback
        self.show('')

    def getNextKeystroke(self, callback):
        self.getNext = callback
        self.show('')

    def processQuotedChar(self, evt):
        """Processor for quoted characters.
        
        This is called from an EVT_CHAR handler so that all the interpretation
        of modifier keys can happen.
        """
        if self.getNext:
            uchar = unichr(evt.GetKeyCode())
            #print("processQuotedChar: %s" % repr(uchar))
            self.getNext(uchar)
            self.getNext = None
            return True
        return False

    def process(self, evt):
        """The main driver routine for keystroke interpretation.
        
        This is called from an EVT_KEY_DOWN handler so that it catches all
        keystrokes individually (including modifier keys) as they occur
        without waiting for wx to interpret them.
        """
        if self.getNext:
            #If we are waiting for a quoted character, skip all keycode
            #processing and let the EVT_CHAR event handle the keystrokes.
            evt.Skip()
            return
        key = self.decode(evt)
#        if self.debug:
#            for keymap in self.keymaps:
#                print keymap.cur
        
        if self.args and key == self.abortKey:
            self.reset()
            self.show("Quit")
        elif self.nextStickyMetaCancel and key==self.stickyMeta:
            # this must be processed before the check for metaNext,
            # otherwise we'll never be able to process the ESC-ESC-ESC
            # quit sequence
            
            if self.processingArgument:
                # If we are in the middle of a keystroke, just cancel
                # the keystroke.
                function = None
            else:
                # If we're not in the middle of the keystroke, also
                # perform the cancel function if there is one.
                skip, unknown, function = self.add(key)
            self.reset()
            if self.reportNext:
                self.reportNext(function)
                self.reportNext = None
            else:
                self.show("Quit")
                if function:
                    function(evt, printable=False)
        elif self.metaNext:
            # OK, the meta sticky key is down, but it's not a quit
            # sequence
            self.show(self.args+self.sofar+" "+self.stickyMeta)
        elif key.endswith('-') and len(key) > 1 and not key.endswith('--'):
            #modifiers only, if we don't skip these events, then when people
            #hold down modifier keys, things get ugly
            evt.Skip()
        elif key==self.universalArgument:
            # signal the start of a numeric argument
            self.startArgument(key)
            self.show(self.args)
        elif not self.processingArgument and self.getNumber(key,musthavectrl=True) is not None:
            # allow Ctrl plus number keys to also start a numeric argument
            self.startArgument()
            self.argument(key)
        else:
            # OK, not one of those special cases.

            if self.processingArgument:
                # if we're inside a numeric argument chain, show it.
                # Note that processingArgument may get reset inside
                # the call to argument()
                self.argument(key)
                self.show(self.args)

            # Can't use an else here because the flag
            # self.processingArgument may get reset inside
            # self.argument() if the key is not a number.  We don't
            # want to lose that keystroke if it isn't a number so
            # process it as a potential hotkey.
            if not self.processingArgument:
                # So, we're not processing a numeric argument now.
                # Check to see where we are in the processing chain.
                skip,unknown,function=self.add(key)
                if function:
                    # Found a function in one of the keymaps, so
                    # execute it.
                    save=self.number
                    printable = not self.modifier
                    self.reset()
                    if self.reportNext:
                        self.reportNext(function)
                        self.reportNext = None
                    else:
                        if self.debug: print("function = %s" % function)
                        if save is not None:
                            function(evt,save, printable=printable)
                        else:
                            function(evt, printable=printable)
                elif unknown:
                    # This is an unknown keystroke combo
                    sf = "%s not defined."%(self.sofar)
                    self.reset()
                    if self.reportNext:
                        self.reportNext(None)
                        self.reportNext = None
                    self.show(sf)
                elif skip:
                    # this is the first keystroke and it doesn't match
                    # anything.  Skip it up to the next event handler
                    # to get processed elsewhere.
                    self.reset()
                    if self.reportNext:
                        self.reportNext(None)
                        self.reportNext = None
                    else:
                        evt.Skip()
                else:
                    self.show(self.args+self.sofar)



if __name__ == '__main__':
    #a utility function and class
    KeyProcessor.debug = True
    
    class StatusUpdater:
        def __init__(self, frame, message):
            self.frame = frame
            self.message = message
        def __call__(self, evt, number=None, **kwargs):
            if number is not None:
                self.frame.SetStatusText("%d x %s" % (number,self.message))
            else:
                self.frame.SetStatusText(self.message)

    class RemoveLocal:
        def __init__(self, frame, message):
            self.frame = frame
            self.message = message
        def __call__(self, evt, number=None):
            self.frame.keys.clearLocalKeyMap()
            self.frame.SetStatusText(self.message)

    class ApplyLocal:
        def __init__(self, frame, message):
            self.frame = frame
            self.message = message
        def __call__(self, evt, number=None):
            self.frame.keys.setLocalKeyMap(self.frame.localKeyMap)
            self.frame.SetStatusText(self.message)

    #The frame with hotkey chaining.

    class MainFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "test")
            self.CreateStatusBar()
            ctrl = self.ctrl = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.WANTS_CHARS|wx.TE_RICH2)
            ctrl.SetFocus()
            ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

            self.globalKeyMap=KeyMap()
            self.localKeyMap=KeyMap()
            self.macKeyMap=KeyMap()
            self.keys=KeyProcessor(status=self)

            menuBar = wx.MenuBar()
            self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
            self.menuBar = menuBar

            self.whichkeymap={}
            gmap = wx.Menu()
            self.whichkeymap[gmap]=self.globalKeyMap
            self.menuAddM(menuBar, gmap, "Global", "Global key map")
            self.menuAdd(gmap, "Open \tC-X\tC-F", "Open File", StatusUpdater(self, "open..."))
            self.menuAdd(gmap, "Save File\tC-X\tC-S", "Save Current File", StatusUpdater(self, "saved..."))
            self.menuAdd(gmap, "Sit \tC-X\tC-X\tC-S", "Sit", StatusUpdater(self, "sit..."))
            self.menuAdd(gmap, "Stay \tC-S\tC-X\tC-S", "Stay", StatusUpdater(self, "stay..."))
            self.menuAdd(gmap, "Execute \tCtrl-C Ctrl-C", "Execute Buffer", StatusUpdater(self, "execute buffer..."))
            self.menuAdd(gmap, "New Frame\tC-x 5 2", "New Frame", StatusUpdater(self, "open new frame"))
            self.menuAdd(gmap, "Help\tCtrl-H", "Help", StatusUpdater(self, "show help"))
            self.menuAdd(gmap, "Help\tShift+Z", "Shift Z", StatusUpdater(self, "Shift Z"))
            self.menuAdd(gmap, "Exit\tC-X C-C", "Exit", sys.exit)

            lmap = wx.Menu()
            self.whichkeymap[lmap]=self.localKeyMap
            self.menuAddM(menuBar, lmap, "Local", "Local key map")
            self.menuAdd(lmap, "Turn Off Local Keymap", "Turn off local keymap", RemoveLocal(self, "local keymap removed"))
            self.menuAdd(lmap, "Turn On Local Keymap", "Turn off local keymap", ApplyLocal(self, "local keymap added"))
            self.menuAdd(lmap, "Comment Region\tC-C C-C", "testdesc", StatusUpdater(self, "comment region"))
            self.menuAdd(lmap, "Stay \tC-S C-X C-S", "Stay", StatusUpdater(self, "stay..."))
            self.menuAdd(lmap, "Multi-Modifier \tC-S-a S-C-m", "Shift-Control test", StatusUpdater(self, "pressed Shift-Control-A, Shift-Control-M"))
            self.menuAdd(lmap, "Control a\tC-A", "lower case a", StatusUpdater(self, "pressed Control-A"))
            self.menuAdd(lmap, "Control b\tC-b", "upper case b", StatusUpdater(self, "pressed Control-B"))
            self.menuAdd(lmap, "Control Shift b\tC-S-b", "upper case b", StatusUpdater(self, "pressed Control-Shift-B"))
            self.menuAdd(lmap, "Control RET\tC-RET", "control-return", StatusUpdater(self, "pressed C-RET"))
            self.menuAdd(lmap, "Control SPC\tC-SPC", "control-space", StatusUpdater(self, "pressed C-SPC"))
            self.menuAdd(lmap, "Control Page Up\tC-PRIOR", "control-prior", StatusUpdater(self, "pressed C-PRIOR"))
            self.menuAdd(lmap, "Control F5\tC-F5", "control-f5", StatusUpdater(self, "pressed C-F5"))
            self.menuAdd(lmap, "Meta-X\tM-x", "meta-x", StatusUpdater(self, "pressed meta-x"))
            self.menuAdd(lmap, "Meta-nothing\tM-", "meta-nothing", StatusUpdater(self, "pressed meta-nothing"))
            self.menuAdd(lmap, "Double Meta-nothing\tM- M-", "meta-nothing", StatusUpdater(self, "pressed meta-nothing"))
            self.menuAdd(lmap, "ESC\tM-ESC ESC", "M-ESC ESC", StatusUpdater(self, "Meta-Escape-Escape"))
            self.menuAdd(lmap, "ESC\tM-ESC A", "M-ESC A", StatusUpdater(self, "Meta-Escape-A"))

            mmap = wx.Menu()
            self.whichkeymap[mmap]=self.macKeyMap
            self.menuAddM(menuBar, mmap, "Mac", "Mac key map")
            self.menuAdd(mmap, "Cut\tCmd-X", "Mac Cut", StatusUpdater(self, "cut..."))
            self.menuAdd(mmap, "Copy\tCmd-C", "Mac Copy", StatusUpdater(self, "copy..."))
            self.menuAdd(mmap, "Paste\tCmd-V", "Mac Paste", StatusUpdater(self, "paste..."))
            self.menuAdd(mmap, "Zippy\t^Z", "Zippy!", StatusUpdater(self, "zippy..."))
            self.menuAdd(mmap, "Zippy\t^X^Z", "Psychoanalize Zippy!", StatusUpdater(self, "psycho zippy..."))
            self.menuAdd(mmap, "Save As...\tShift-Cmd-S", "Save As", StatusUpdater(self, "save as..."))
            self.menuAdd(mmap, "Show Toolbar...\tOption-Cmd-T", "Toolbar", StatusUpdater(self, "show toolbar..."))
            self.menuAdd(mmap, "Option test\tOption-N", "Option N", StatusUpdater(self, "Option N..."))

            #print self.lookup
            self.keys.setGlobalKeyMap(self.globalKeyMap)
            self.keys.setLocalKeyMap(self.localKeyMap)
            self.keys.addMinorKeyMap(self.macKeyMap)
            print self.localKeyMap.getBindings()
            print self.globalKeyMap.getBindings()
            self.Show(1)


        def menuAdd(self, menu, name, desc, fcn, id=-1, kind=wx.ITEM_NORMAL):
            if id == -1:
                id = wx.NewId()
            a = wx.MenuItem(menu, id, 'TEMPORARYNAME', desc, kind)
            menu.AppendItem(a)
            wx.EVT_MENU(self, id, fcn)

            def _spl(st):
                if '\t' in st:
                    return st.split('\t', 1)
                return st, ''

            ns, acc = _spl(name)

            if acc:
                if menu in self.whichkeymap:
                    keymap=self.whichkeymap[menu]
                else:
                    # menu not listed in menu-to-keymap mapping.  Put in
                    # local
                    keymap=self.localKeyMap
                keymap.define(acc, fcn)

                acc=acc.replace('\t',' ')
                #print "acc=%s" % acc
                
                # The "append ascii zero to the end of the accelerator" trick
                # no longer works for windows, so use the same hack below for
                # all platforms.

                # wx doesn't allow displaying arbitrary text as the
                # accelerator, so we have format it according to what's
                # allowed by the current platform.  Emacs style multi-
                # keystroke bindings are not right-aligned, unfortunately.
                acc_text = KeyAccelerator.getAcceleratorText(acc)
                menu.SetLabel(id, "%s%s" % (ns, acc_text))
            else:
                menu.SetLabel(id,ns)
            menu.SetHelpString(id, desc)

        def menuAddM(self, parent, menu, name, help=''):
            if isinstance(parent, wx.Menu):
                id = wx.NewId()
                parent.AppendMenu(id, "TEMPORARYNAME", menu, help)

                self.menuBar.SetLabel(id, name)
                self.menuBar.SetHelpString(id, help)
            else:
                parent.Append(menu, name)

        def OnKeyPressed(self, evt):
            print "in OnKeyPressed"
            self.keys.process(evt)
    
    app = wx.PySimpleApp()
    frame = MainFrame()
    app.MainLoop()
