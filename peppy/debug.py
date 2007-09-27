# peppy Copyright (c) 2006-2007 Rob McMullen
# Licenced under the GPL; see http://www.flipturn.org/peppy for more info
"""
Debug mixin and debug printing based on class hierarchy.

NOTE: inspect.stack() is used to determine the class hierarchy at
runtime.  When using py2exe this call takes a very long time, on the
order of tenths of seconds!  So, beware to turn off most debug
printing when deploying the application.
"""

import os,sys,inspect

dlogfh=sys.stderr
elogfh=sys.stderr

__all__ = ['debuglog', 'errorlog', 'dprint', 'eprint', 'debugmixin',
           'get_all_objects', 'get_all_referrers']

# Found an obscure bug while working on Windows: the call to dprint
# was failing in Peppy.getConfigFilePath when called from
# boa.getUserConfigFile because the call to inspect.callers() was
# throwing an IndexError.  Found a reference to that being a bug in
# Python's inspect module:

# http://lists.xensource.com/archives/html/xen-users/2007-03/msg00713.html
# Work around a bug in Python's inspect module: findsource is supposed
# raise IOError if it fails, with other functions in that module
# coping with that, but some people are seeing IndexError raised from
# there.
if hasattr(inspect, 'findsource'):
    real_findsource = getattr(inspect, 'findsource')
    def findsource(*args, **kwargs):
        try:
            return real_findsource(*args, **kwargs)
        except IndexError, exn:
            raise IOError(exn)
    inspect.findsource = findsource

def debuglog(file):
    global dlogfh
    if hasattr(file, 'write'):
        dlogfh = file
    else:
        dlogfh=open(file,"w")

def errorlog(file):
    global elogfh
    if hasattr(file, 'write'):
        elogfh = file
    else:
        elogfh=open(file,"w")

def dprint(str=''):
    caller=inspect.stack()[1]
    try:
        namespace=caller[0].f_locals
        if 'self' in namespace:
            cls=namespace['self'].__class__.__name__+'.'
        else:
            cls=''
        dlogfh.write("%s:%d %s%s: %s%s" % (os.path.basename(caller[1]),caller[2],cls,caller[3],str,os.linesep))
    finally:
        del caller
    return True

def eprint(str=''):
    caller=inspect.stack()[1]
    try:
        namespace=caller[0].f_locals
        if 'self' in namespace:
            cls=namespace['self'].__class__.__name__+'.'
        else:
            cls=''
        elogfh.write("%s:%d %s%s: %s%s" % (os.path.basename(caller[1]),caller[2],cls,caller[3],str,os.linesep))
    finally:
        del caller
    return True

class debugmixin(object):
    debuglevel=0

    @classmethod
    def dprint(cls,str='',level=1):
        if not hasattr(cls, 'debuglevel') or cls.debuglevel>=level:
            caller=inspect.stack()[1]
            try:
                dlogfh.write("%s:%d %s.%s: %s%s" % (os.path.basename(caller[1]),caller[2],cls.__name__,caller[3],str,os.linesep))
            finally:
                del caller
        return True

##    def dprint(self,str='',level=1):
##        if not hasattr(self,'debuglevel') or self.debuglevel>=level:
##            caller=inspect.stack()[1]
##            dlogfh.write("%s:%d %s.%s: %s%s" % (os.path.basename(caller[1]),caller[2],caller[0].f_locals['self'].__class__.__name__,caller[3],str,os.linesep))
##        return True

# Get a list of "all" objects as seen by the garbage collector.
# Snarfed this code from
# http://utcc.utoronto.ca/~cks/space/blog/python/GetAllObjects and
# also see
# http://utcc.utoronto.ca/~cks/space/blog/python/GetAllObjectsII for
# more info.

import gc

# Recursively expand slist's objects into olist, using seen to track
# already processed objects.
def _getr(slist, olist, seen):
    for e in slist:
        if id(e) in seen:
            continue
        seen[id(e)] = None
        olist.append(e)
        tl = gc.get_referents(e)
        if tl:
            _getr(tl, olist, seen)

# The public function.
def get_all_objects(subclassof=None):
    """Return a list of all live Python objects, not including the
    list itself."""
    gcl = gc.get_objects()
    olist = []
    seen = {}
    # Just in case:
    seen[id(gcl)] = None
    seen[id(olist)] = None
    seen[id(seen)] = None
    # _getr does the real work.
    _getr(gcl, olist, seen)
    if subclassof is not None:
        nlist=olist
        olist=[]
        for obj in nlist:
            if isinstance(obj,subclassof): olist.append(obj)
    return olist

def get_all_referrers(subclassof=None):
    olist=get_all_objects(subclassof)
    for obj in olist:
        referrers=gc.get_referrers(obj)
        print ">>> %s: " % obj
        others=[]
        for ref in referrers:
            if isinstance(ref,dict) or isinstance(ref,list):
                print ">>>    %s" % ref
            else:
                others.append(ref.__class__)
        print ">>>    %s" % str(others)
    

if __name__=="__main__":
    dprint('testing')
    
    class test(debugmixin):
        debuglevel=1

        def method(self):
            assert self.dprint('need classname')

    t=test()
    t.method()


