# peppy Copyright (c) 2006-2007 Rob McMullen
# Licenced under the GPL; see http://www.flipturn.org/peppy for more info

from peppy.yapsy.plugins import *

from peppy.debug import *

from peppy.hsi.loader import *

class HSIPlugin(IPeppyPlugin):
    """HSI viewer plugin to register modes and user interface.
    """

    def attemptOpen(self, url):
        dprint("Trying to open url: %s" % url)
        hsi_major_mode = self.importModule("hsi_major_mode")
        if hsi_major_mode:
            format = HyperspectralFileFormat.identify(url)
            if format:
                dprint("found %s" % format)
                return hsi_major_mode.HSIMode
        return None
    
    def getCompatibleMajorModes(self, stc_class):
        if stc_class == HyperspectralSTC:
            hsi_major_mode = self.importModule("hsi_major_mode")
            if hsi_major_mode:
                return [hsi_major_mode.HSIMode]
        return []

    def getCompatibleMinorModes(self, cls):
        if cls.keyword == "HSI":
            hsi_major_mode = self.importModule("hsi_major_mode")
            if hsi_major_mode:
                for mode in [hsi_major_mode.HSIXProfileMinorMode,
                             hsi_major_mode.HSIYProfileMinorMode,
                             hsi_major_mode.HSISpectrumMinorMode]:
                    yield mode
        raise StopIteration
    
    def getCompatibleActions(self, cls):
        dprint("Checking for HSI mode %s" % cls)
        if cls.keyword == "HSI":
            hsi_major_mode = self.importModule("hsi_major_mode")
            if hsi_major_mode:
                return [hsi_major_mode.PrevCube,
                        hsi_major_mode.NextCube,
                        hsi_major_mode.SelectCube,
                        hsi_major_mode.PrevBand,
                        hsi_major_mode.NextBand,
                        hsi_major_mode.GotoBand,
                        hsi_major_mode.ContrastFilterAction,
                        hsi_major_mode.MedianFilterAction,
                        hsi_major_mode.CubeViewAction,
                        ]
        return []
