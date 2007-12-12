import os

from peppy.vfs.itools.datatypes import FileName
from peppy.vfs.itools.vfs import *
from peppy.vfs.itools.vfs.registry import get_file_system, deregister_file_system
from peppy.vfs.itools.uri import *
from peppy.vfs.itools.vfs.base import BaseFS

import peppy.vfs.mem
import peppy.vfs.http
import peppy.vfs.tar

from peppy.debug import *

def normalize(ref, base=None):
    """Normalize a url string into a reference and fix windows shenanigans"""
    if not isinstance(ref, Reference):
        ref = get_reference(ref)
    # Check the reference is absolute
    if ref.scheme:
        return ref
    # Default to the current working directory
    if base is None:
        base = os.getcwd()
    
    # URLs always use /
    if os.path.sep == '\\':
        base = base.replace(os.path.sep, '/')
    # Check windows drive letters
    if base[1] == ':':
        base = "%s:%s" % (base[0].lower(), base[2:])
    baseref = get_reference('file://%s/' % base)
    return baseref.resolve(ref)

def canonical_reference(ref):
    """Normalize a uri but remove any query string or fragments."""
    # get a copy of the reference
    ref = normalize(str(ref))
    ref.query = {}
    ref.fragment = ''
    
    # make sure that any path that points to a folder ends with a slash
    if is_folder(ref):
        ref.path.endswith_slash = True
    return ref
    

# Simple cache of wrappers around local filesystem objects.
cache = {}
max_cache = 5
def remove_from_cache(fstype, path):
    if fstype in cache:
        subcache = cache[fstype]
        newlist = []
        for saved_path, saved_mtime, obj in subcache:
            if path != saved_path:
                newlist.append((saved_path, saved_mtime, obj))
        cache[fstype] = newlist

def find_local_cached(fstype, path):
    if fstype in cache:
        subcache = cache[fstype]
        for i in range(len(subcache)):
            saved_path, saved_mtime, obj = subcache[i]
            #dprint("path=%s: checking %s: mtime=%s" % (path, saved_path, saved_mtime))
            if path == saved_path:
                try:
                    mtime = os.path.getmtime(path)
                    if mtime > saved_mtime:
                        #dprint("modification time changed: %s to %s for %s" % (saved_mtime, mtime, path))
                        remove_from_cache(fstype, path)
                    else:
                        #dprint("found match %s" % saved_path)
                        return obj
                except:
                    import traceback
                    #traceback.print_exc()
                    #print("Exception: %s" % str(e))
                    remove_from_cache(fstype, path)
                return None
    return None
BaseFS.find_local_cached = staticmethod(find_local_cached)

def store_local_cache(fstype, path, obj):
    if fstype not in cache:
        cache[fstype] = []
    subcache = cache[fstype]
    # new items inserted at the beginning of the list
    subcache[0:0] = [(path, os.path.getmtime(path), obj)]
    print subcache
    # truncate the list if it's getting too big.
    if len(subcache) > max_cache:
        subcache = subcache[0:max_cache]
    
BaseFS.store_local_cache = staticmethod(store_local_cache)


__all__ = [
    ##### From vfs:
    'BaseFS',
    'FileFS',
    # File modes
    'READ',
    'WRITE',
    'APPEND',
    # Registry
    'register_file_system',
    'deregister_file_system',
    'get_file_system',
    # Functions
    'exists',
    'is_file',
    'is_folder',
    'can_read',
    'can_write',
    'get_ctime',
    'get_mtime',
    'get_atime',
    'get_mimetype',
    'get_size',
    'make_file',
    'make_folder',
    'remove',
    'open',
    'copy',
    'move',
    'get_names',
    'traverse',

    ##### From uri:
    'get_reference',
    'normalize',
    'canonical_reference',
    ]