#!/usr/bin/env python

# Relatively generic setup.py that should be easily tailorable to other python
# modules.  It gets most of the parameters from the packaged module itself, so
# this file shouldn't have to be changed much.

import os,sys,distutils, glob
from distutils.core import setup, Extension

if sys.version < '2.3':
    raise SystemExit('Sorry, peppy requires at least Python 2.3 because wxPython does.')

# ignore a warning about large int constants in Python 2.3.*
if sys.version >= '2.3' and sys.version < '2.4':
    import warnings
    warnings.filterwarnings('ignore', "hex/oct constants", FutureWarning)


try:
    import py2exe
    USE_PY2EXE = True
except:
    USE_PY2EXE = False
    
# Manifest file to allow py2exe to use the winxp look and feel
manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>Your Application</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

# use windows batch files if we're on windows
scripts = ['scripts/peppy']
from distutils import util
if util.get_platform()[:3] == 'win':
    scripts = [script + '.bat' for script in scripts]

# set up extension modules
ext_modules = []
include_dirs = []

# check NumPy support for building the hsi extension module
HAVE_NUMPY=False
try:
    import numpy
    HAVE_NUMPY=True

    # Function to find numpy's include directory; code snarfed from
    # GDAL's setup.py
    def get_numpy_include():
        for directory in sys.path:
            d = os.walk(directory)
            for i in d:
                if 'numpy' in i[0]:
                    if 'core' in i[0]:
                        if 'include' in i[0]:
                            return i[0]
        return '.'
    
    numpy_include = get_numpy_include()
    print 'numpy include = %s' % numpy_include
    if numpy_include =='.':
        print "numpy headers were not found!  Fast array support will not be enabled."
        HAVE_NUMPY=False
    else:
        include_dirs.append(numpy_include)
        numarray_compat = os.path.join(os.path.dirname(os.path.dirname(numpy_include)),'numarray','numpy')
        include_dirs.append(numarray_compat)
except ImportError:
    pass

if HAVE_NUMPY and not USE_PY2EXE:
    # Don't try building extension modules when using py2exe, because
    # I don't have the correct microsoft compiler
    ext_modules.append(Extension('peppy.hsi._utils',
                                 sources = ['peppy/hsi/_utils.c'],
                                 include_dirs = include_dirs,
                                 ))

# Create the data files for Editra's styling
DATA_FILES = [("peppy/editra/styles", glob.glob("peppy/editra/styles/*.ess")),
              ("peppy/editra/tests", glob.glob("peppy/editra/tests/*")),
              ("peppy/editra/syntax", glob.glob("peppy/editra/syntax/*.*"))]

setup(name = 'peppy',
      version = '0.7.0',
      description = '(ap)Proximated (X)Emacs Powered by Python',
      long_description = 'An experiment using the modern software development process -- this is a wxPython/Scintilla-based editor written in and extensible through Python. It attempts to provide an XEmacs-like multi-window, multi-tabbed interface using the Advanced User Interface (wx.aui) framework of wxPython.',
      keywords = 'text editor, wxwindows, scintilla',
      license = 'GPL',
      author = 'Rob McMullen',
      author_email = 'robm@users.sourceforge.net',
      url = 'http://peppy.flipturn.org/',
      download_url = 'http://peppy.flipturn.org/archive/',
      platforms='any',
      scripts=scripts,
      packages = ['peppy', 'peppy.actions', 'peppy.extensions', 'peppy.hsi',
                  'peppy.lib', 'peppy.nltk_lite', 'peppy.nltk_lite.chat',
                  'peppy.nltk_lite.chat.nltk_lite', 'peppy.plugins',
                  'peppy.plugins.games', 'peppy.pype', 'peppy.vfs',
                  'peppy.yapsy', 'peppy.editra', 'peppy.editra.syntax'],
      ext_modules = ext_modules,

      # FIXME: the excludes option still doesn't work.  py2exe still
      # picks up a bunch of unnecessary stuff that I'm trying to get
      # rid of.
      options = {'py2exe': {'unbuffered': True,
                            'optimize': 2,
                            'excludes': ['Tkinter', 'Tkconstants', 'tcl', '_tkinter', 'numpy.distutils', 'numpy.f2py', 'matplotlib', 'doctest'],
                            }
                 },
      windows = [{"script": "peppy.py",
                  "other_resources": [(24,1,manifest)],
                  "icon_resources": [(2, "../graphics/peppy48.ico")],
                  }
                  ],
      data_files = DATA_FILES,
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: MacOS X',
                   'Environment :: Win32 (MS Windows)',
                   'Environment :: X11 Applications',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   'Operating System :: POSIX :: Linux',
                   'Operating System :: Unix',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Documentation',
                   'Topic :: Text Editors',
                   ]
      )
