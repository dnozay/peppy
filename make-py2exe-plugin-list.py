#!/usr/bin/env python

import os, shutil, sys, glob
import __builtin__
from cStringIO import StringIO
from optparse import OptionParser

__builtin__._ = str

plugin_count = 0

lastfake = False

def entry(filename, out=None, copythese=None, fake=False):
    print "Processing filename %s" % filename
    if filename.endswith(".py"):
        if copythese is not None and not fake:
            copythese.append(filename)
        if not filename.endswith("__init__.py") or True:
            module = filename[:-3].replace('/', '.').replace('\\', '.')
            if out:
                if fake:
                    global lastfake
                    if lastfake:
                        out.write("    ")
                    else:
                        out.write("if False: # fake the import so py2exe will include the file\n    ")
                        lastfake = True
                else:
                    global lastfake
                    lastfake = False
                    global plugin_count
                    plugin_count += 1
                    out.write("app.gaugeCallback('%s')\n" % module)
                print "importing %s" % module
                out.write("import %s\n" % (module))

def process(path, out=None, copythese=None, fake=False):
    files = glob.glob('%s/*' % path)
    for path in files:
        if os.path.isdir(path):
            process(path, out, fake=fake)
        else:
            entry(path, out, copythese, fake)

def load_setuptools_plugins(entry_point_name, out, packages):
    modules_seen = {}
    
    for entrypoint in pkg_resources.iter_entry_points(entry_point_name):
        print "entrypoint: %s" % entrypoint
        # Don't load plugin class becasue classprefs depend on wx
        #plugin_class = entrypoint.load()
        plugin_class = None
        print "module name: %s" % entrypoint.module_name
        print "entrypoint=%s, name=%s, class=%s" % (entrypoint, entrypoint.name, plugin_class)

        # find the parent of the loaded module
        moduleparent, module = entrypoint.module_name.rsplit('.', 1)
        print "moduleparent=%s" % moduleparent
        if moduleparent not in packages:
            packages.append(moduleparent)
        
        # import that module (which, since it's a module, imports
        # its __init__.py)
        m = __import__(moduleparent)
        print m.__file__
        path = m.__file__
        print "module path=%s" % path
        if path in modules_seen:
            print "Already seen %s" % path
            continue
        modules_seen[path] = True

        # from its file, get the directory that contains the __init__.py
        path = os.path.dirname(m.__file__)
        print path

        # go up one directory
        path = os.path.dirname(path)
        print path
        os.chdir(path)
        copythese = []
        process(moduleparent, out, copythese)
        os.chdir(savepath)

        print "copying: %s" % str(copythese)
        for py in copythese:
            source = os.path.join(path, py)
            dest = os.path.join(savepath, py)
            try:
                print "mkdir %s" % os.path.dirname(dest)
                os.makedirs(os.path.dirname(dest))
            except:
                pass
            shutil.copy(source, dest)
            print "cp %s %s" % (source, dest)
    

if __name__ == "__main__":
    usage="usage: %prog [-s dir] [-o file]"
    parser=OptionParser(usage=usage)
    parser.add_option("-s", action="store_true", dest="setuptools", default=False,
                      help="copy and include setuptools plugins into the base directory")
    parser.add_option("-i", action="store", dest="input",
                      default="peppy", help="base input directory")
    parser.add_option("-d", action="store", dest="importdir",
                      default="builtins", help="import directory within base directory")
    parser.add_option("-o", action="store", dest="output",
                      default="peppy/py2exe_plugins.py", help="output filename")
    (options, args) = parser.parse_args()

    out = StringIO()
    out.write("# Automatically generated, and only used when creating a py2exe distribution\n")

    os.chdir(options.input)
    savepath = os.getcwd()
    destdir = os.path.join(savepath, options.importdir)
    print destdir

    setuptools_packages = []
    if options.setuptools:
        try:
            import pkg_resources
            load_setuptools_plugins('peppy.plugins', out, setuptools_packages)
            load_setuptools_plugins('peppy.hsi.plugins', out, setuptools_packages)
        except:
            raise

    os.chdir(savepath)

    process(options.importdir, out)
    # Need to fake the importing of the editra style definition files so py2exe
    # will include them
    process('peppy/editra/syntax', out, fake=True)

    filename = os.path.join(savepath, options.output)
    fh = open(filename, 'w')
    fh.write("import wx\napp = wx.GetApp()\n")
    fh.write(out.getvalue())
    fh.close()
    
    countname = filename.replace(".py", "_count.py")
    fh = open(countname, 'w')
    fh.write("count = %d\n" % plugin_count)
    if setuptools_packages:
        fh.write("setuptools_packages = %s\n" % repr(setuptools_packages))
    fh.close()
