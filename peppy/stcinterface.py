# peppy Copyright (c) 2006-2007 Rob McMullen
# Licenced under the GPL; see http://www.flipturn.org/peppy for more info


#### STC Interface

class STCInterface(object):
    """
    Methods that a data source object must implement in order to be
    compatible with the real STC used as the data source for
    text-based files.

    See U{the Yellowbrain guide to the
    STC<http://www.yellowbrain.com/stc/index.html>} for more info on
    the rest of the STC methods.
    """
    def CanEdit(self):
        """PyPE compat to show read-only status"""
        return True
    
    def CanSave(self):
        """Can this STC instance save its contents?"""
        return True
    
    def Clear(self):
        pass

    def CanCopy(self):
        return False

    def Copy(self):
        pass

    def CanCut(self):
        return False

    def Cut(self):
        pass

    def CanPaste(self):
        return False

    def Paste(self):
        pass

    def EmptyUndoBuffer(self):
        pass

    def CanUndo(self):
        return False

    def Undo(self):
        pass

    def CanRedo(self):
        return False

    def Redo(self):
        pass

    def SetSavePoint(self):
        pass

    def GetText(self):
        return ''
    
    def GetLength(self):
        return 0
    
    GetTextLength = GetLength

    def GetModify(self):
        return False

    def CreateDocument(self):
        return "notarealdoc"

    def SetDocPointer(self,ptr):
        pass

    def ReleaseDocument(self,ptr):
        pass

    def AddRefDocument(self,ptr):
        pass

    def GetBinaryData(self,start,end):
        return []

    def GuessBinary(self,amount,percentage):
        return False

    def getShortDisplayName(self, url):
        """Return a short name for display in tabs or other context without
        needing a pathname.
        """
        return url.path.get_name()

    def open(self, buffer, message=None):
        """Read from the specified url to populate the STC.
        
        Abstract method that subclasses use to read data into the STC.

        buffer: buffer object used to read the file
        
        message: optional message used to update a progress bar
        """
        pass

    def readFrom(self, fh):
        """Read from filehandle, converting as necessary

        @param fh: file-like object used to load the file
        """
        pass

    def writeTo(self, fh):
        """Write to filehandle, converting as necessary

        @param fh: file-like object used to write the file
        """
        pass

    def showStyle(self, linenum=None):
        """Debugging routine to show the styling information on a line.

        Print styling information to stdout to aid in debugging.
        """
        pass

    def GetFoldLevel(self, line):
        """Return fold level of specified line.

        Return fold level of line, which seems to be the number of spaces used
        to indent the line, plus an offset and shifted by 2^10
        """
        return 1024

    def GetFoldColumn(self, line):
        """Return column number of folding.

        Return column number of the current fold level.
        """
        return 0

    def GetPrevLineIndentation(self, line):
        """Get the indentation of the line before the specified line.

        Return a tuple containing the number of columns of indentation
        of the first non-blank line before the specified line, and the
        line number of the line that it found.
        """
        return 0, -1

    def GotoPos(self, pos):
        """Move the cursor to the specified position and scroll the
        position into the view if necessary.
        """
        pass

class STCProxy(object):
    """Proxy object to defer requests to a real STC.

    Used to wrap a real STC but supply some custom methods.  This is
    used in the case where the major mode is using a real stc for its
    data storage, but not using the stc for display.  Because the
    major mode depends on an stc interface to manage the user
    interface (enabling/disabling buttons, menu items, etc.), a mode
    that doesn't use the stc for display still has to present an stc
    interface for this purpose.  So, wrapping the buffer's stc in this
    object and reassigning methods as appropriate for the display is
    the way to go.
    """
    def __init__(self, stc):
        self.stc = stc

    def __getattr__(self, name):
        # can't use self.stc.__dict__ because the stc is a swig object
        # and apparently swig attributes don't show up in __dict__.
        # So, this is probably slow.
        if hasattr(self.stc, name):
            return getattr(self.stc, name)
        raise AttributeError


class NonResidentSTC(STCInterface):
    """Non-memory-resident version of the STC.
    
    Base version of a non-memory resident storage space that
    implements the STC interface.
    """
    debuglevel=0
    
    def __init__(self, parent=None, copy=None):
        self.filename = None

    def CanEdit(self):
        return False
    
    def Destroy(self):
        pass
    
