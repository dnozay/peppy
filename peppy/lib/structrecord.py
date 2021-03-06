# peppy Copyright (c) 2006-2010 Rob McMullen
# Licenced under the GPLv2; see http://peppy.flipturn.org for more info
"""StructRecord -- a binary record packer/unpacker

This module unpacks binary records into objects, and packs objects
into binary records.  Similar in spirit to Construct (on the web at
construct.wikispaces.com), but assembles parsed data into objects
instead of construct's unnamed data structures.

Allows conditionals, recursive definition of structures, and custom
pack/unpack classes.  A class to store unparsed binary data needs a
class attribute named 'typedef' that is a tuple that defines the
structure of the binary record.  The tuple contains a description of
the entities in the binary record, in order that they occur in the
file.

Simple example for parsing 3 32-bit integers of varying endianness:

    class TestParse:
        typedef=(
            FormatField('testi1','<i'),
            SLInt32('testi2'),
            SBInt32('testi3'),
            )

More complicated examples include conditionals, cases, lists, and nested
structures.  For more examples, see the unit tests.
"""


import os,sys,re
import struct
from cStringIO import StringIO
import copy
import pprint

try:
    from peppy.debug import *
except:
    import inspect
    
    def dprint(str=''):
        caller=inspect.stack()[1]
        namespace=caller[0].f_locals
        if 'self' in namespace:
            cls=namespace['self'].__class__.__name__+'.'
        else:
            cls=''
        logfh.write("%s:%d %s%s: %s%s" % (os.path.basename(caller[1]),caller[2],cls, caller[3],str,os.linesep))
        return True

    class debugmixin(object):
        debuglevel=0

        def dprint(self,str='',level=1):
            if not hasattr(self,'debuglevel') or self.debuglevel>=level:
                caller=inspect.stack()[1]
                logfh.write("%s:%d %s.%s: %s%s" % (os.path.basename(caller[1]),caller[2],caller[0].f_locals['self'].__class__.__name__,caller[3],str,os.linesep))
            return True
    

debug=True

# base indent level when printing stuff
base_indent="    "

def repr1(name,value,indent, printall=False):
    if isinstance(value,Field):
        txt=value._getString(indent)
    elif isinstance(value,list):
        stuff=[]
        print_all = False
        for item in value:
            if isinstance(item,Field):
                stuff.append(item._getString(indent+base_indent))
            else:
                stuff.append("%s%s" % (indent+base_indent,repr(item)))
        if printall==False and len(stuff)>10:
            stuff[2:-2]=["\n%s..." % (indent+base_indent)]
        txt="%s%s = [\n%s\n%s]" % (indent,name,",\n".join(stuff),indent)
    else:
        txt="%s%s = %s" % (indent,name,repr(value))
    return txt

def repr2(name, value, prefix, printall=False):
    if isinstance(value,Field):
        txt=value._getDottedString(prefix)
    elif isinstance(value,list):
        stuff=[]
        print_all = False
        index = 0
        for item in value:
            if isinstance(item,Field):
                stuff.append(item._getDottedString(prefix, index=index))
            else:
                stuff.append("%s.%s[%d] = %s" % (prefix, name, index, repr(item)))
            index += 1
        if printall==False and len(stuff)>10:
            stuff[2:-2]=["\n%s..." % (indent+base_indent)]
        txt = "\n".join(stuff)
    else:
        txt="%s.%s = %s" % (prefix,name,repr(value))
    return txt
    

class FieldError(Exception):
    pass

class FieldTypedefError(Exception):
    pass

class FieldLengthError(FieldError):
    pass

class FieldNameError(FieldError):
    pass

class FieldAbortError(FieldError):
    pass


class Field(debugmixin):
    debuglevel = 0
    print_all = False
    
    def __init__(self,name,default=None):
        if name is not None and name.startswith("_"):
            raise FieldNameError("attribute names may not start with '_'")
        self._name=name
        self._default=default

    def getCopy(self,obj):
        return copy.copy(self)
    
    def getDefault(self, obj):
        return copy.copy(self._default)

    def storeDefault(self,obj):
        # make a copy of the default value, in case the default
        # specified is not a primitive object.
        setattr(obj, self._name, self.getDefault(obj))
        
    def getNumBytes(self,obj):
        return 0

    def read(self,fh,obj):
        expected=self.getNumBytes(obj)
        data=fh.read(expected)
        if len(data)<expected:
            raise EOFError("End of unserializable data in %s" % self._name)
        return data

    def unpack(self,fh,obj):
        raise NotImplementedError()

    def pack(self,fh,obj):
        raise NotImplementedError()

    def _getString(self,indent=""):
        names=self.__dict__.keys()
        names.sort()
        lines=["%s%s %s:" % (indent,repr(self),self._name)]
        if "_print_all" in self.__dict__ or self.print_all:
            printall = True
        else:
            printall = False
        for name in names:
            # ignore all keys that start with an underscore
            if not name.startswith("_"):
                value=self.__dict__[name]
                lines.append(repr1(name,value,indent+base_indent, printall))
        if "_" in self.__dict__.keys():
            lines.append("%s_ = %s" % (indent+base_indent,repr(self.__dict__["_"])))
        return "\n".join(lines)

    def __str__(self):
        #pp=pprint.PrettyPrinter(indent=4)
        #return pp.pformat(self)
        return self._getString()


class NoOp(Field):
    def unpack(self,fh,obj):
        setattr(obj,self._name,None)
        
    def pack(self,fh,obj):
        pass
        
class Abort(Field):
    def unpack(self,fh,obj):
        raise FieldAbortError(self._name)
        
    def pack(self,fh,obj):
        raise FieldAbortError(self._name)
        

class MetaField(Field):
    def __init__(self,name,func,default=None):
        Field.__init__(self,name,default)
        self._func=func

    def getNumBytes(self,obj):
        return self._func(obj)

    def unpack(self,fh,obj):
        try:
            data=self.read(fh,obj)
            setattr(obj,self._name,data)
        except Exception:
            dprint("FAILED: %s" % self)
            raise

    def pack(self,fh,obj):
        try:
            value=getattr(obj,self._name)
            fh.write(value)
        except Exception:
            dprint("FAILED: %s" % self)
            raise

class Skip(MetaField):
    debuglevel=0
    count=0
    
    def __init__(self,func,padding='\0',write=None):
        Skip.count+=1
        self._padding=padding
#        MetaField.__init__(self,"skip%d" % Skip.count,func,None)
        MetaField.__init__(self,None,func,None)
        self._writefunc=write

    def storeDefault(self,obj):
        pass
    
    def unpack(self,fh,obj):
        offset=self.getNumBytes(obj)
        # skip over the data entirely; don't even try to read it
        fh.seek(offset,1)
        
    def pack(self,fh,obj):
        if self._writefunc:
            self._writefunc(obj,fh,self.getNumBytes(obj))
        else:
            data=self._padding*self.getNumBytes(obj)
            fh.write(data)

class CString(Field):
    def __init__(self,name,func=None,default=None):
        Field.__init__(self,name,default)
        self._func=func
        self._terminator='\x00'

        # _length is the number of bytes in the binary file, not the
        # number of bytes in the string.  This means that _length
        # INCLUDES THE TERMINATOR CHARACTER(S)!!!
        self._length=None

    def getNumBytes(self,obj):
        if self._func is not None:
            return self._func(obj)
        if self._length is not None:
            return self._length
        raise FieldLengthError('CString %s has unknown length until unpacked')

    def unpack(self,fh,obj):
        data=StringIO()
        self._length=0
        if self._func is not None:
            maxlen=self._func(obj)
        else:
            maxlen=-1 # Note: any negative number evaluates to True
        while maxlen:
            char=fh.read(1)
            self._length+=1
            maxlen-=1
            if char==self._terminator:
                break
            data.write(char)
        setattr(obj,self._name,data.getvalue())

        # If a length function has been specified and we're not there
        # yet, space foreward, skipping over junk
        if maxlen>0:
            fh.read(maxlen)

    def pack(self,fh,obj):
        value=getattr(obj,self._name)
        terminators=self._terminator

        # check if a field length is specified.
        if self._func is not None:
            maxlen=self._func(obj)
            valuelen=len(value) # don't include space for the terminator here
            if valuelen>=maxlen:
                value=value[0:maxlen-len(terminators)]
            elif valuelen<maxlen:
                # pad the binary file with extra terminators if necessary
                terminators=self._terminator*(maxlen-valuelen)
        fh.write(value)
        fh.write(terminators) # terminator always added here
        self._length=len(value)+len(terminators)




class FormatField(Field):
    def __init__(self,name,fmt,default=None):
        Field.__init__(self,name,default)
        self._fmt=fmt
        self._size=struct.calcsize(fmt)

    def getNumBytes(self,obj):
        return self._size

    def unpack(self,fh,obj):
        try:
            data=self.read(fh,obj)
            setattr(obj,self._name,struct.unpack(self._fmt,data)[0])
        except Exception:
            dprint("FAILED: %s" % self)
            raise

    def pack(self,fh,obj):
        try:
            value=getattr(obj,self._name)
            if self._fmt.endswith('s'):
                if len(value)<self._size:
                    value+=' '*(self._size-len(value))
                elif len(value)>self._size:
                    value=value[0:self._size]
            fh.write(struct.pack(self._fmt,value))
        except Exception:
            dprint("FAILED: %s" % self)
            raise


class Wrapper(Field):
    def __init__(self,proxy):
        Field.__init__(self,proxy._name,proxy._default)
        self._proxy=proxy

    def getProxy(self,obj):
        return self._proxy

    def storeDefault(self,obj):
        proxy=self.getProxy(obj)
        if isinstance(proxy,Record):
            assert self.debuglevel == 0 or self.dprint("calling %s.storeDefault(obj.%s)" % (str(proxy),proxy._name))
            setattr(obj,self._name,proxy.getCopy(obj))
            assert self.debuglevel == 0 or self.dprint("copy of %s = %s" % (self._name,getattr(obj,self._name)))
            child=getattr(obj,self._name)
            # set obj._ to be obj for parent object reference
            assert self.debuglevel == 0 or self.dprint("child=%s" % child.__class__.__name__)
            setattr(child,"_",obj)
        else:
            proxy.storeDefault(obj)
        
    def getNumBytes(self,obj):
        proxy=self.getProxy(obj)
        if isinstance(proxy,Record):
            assert self.debuglevel == 0 or self.dprint("calling %s.getNumBytes(obj.%s) proxy._name=%s" % (str(proxy),self._name,proxy._name))
            length=proxy.getNumBytes(getattr(obj,self._name))
        else:
            length=proxy.getNumBytes(obj)
        return length

    def unpack(self,fh,obj):
        proxy=self.getProxy(obj)
        if isinstance(proxy,Record):
            # check to see if the proxy object has changed, and if so
            # change the object that's stored in the parent to match
            # the proxy object.
            current=getattr(obj,self._name)
            if not isinstance(current,proxy.__class__):
                assert self.debuglevel == 0 or self.dprint("proxy has changed from %s to %s" % (current.__class__.__name__,proxy.__class__.__name__))
                self.storeDefault(obj)
            
            assert self.debuglevel == 0 or self.dprint("calling %s.unpack(obj.%s)" % (str(proxy),proxy._name))
            proxy.unpack(fh,getattr(obj,self._name))
        else:
            proxy.unpack(fh,obj)

    def pack(self,fh,obj):
        proxy=self.getProxy(obj)
        if isinstance(proxy,Record):
            assert self.debuglevel == 0 or self.dprint("calling %s.pack(obj.%s)" % (str(proxy),proxy._name))
            proxy.pack(fh,getattr(obj,self._name))
        else:
            proxy.pack(fh,obj)


class Switch(Wrapper):
    def __init__(self,name,func,switch,default=None):
        if default is None:
            default=NoOp(name)
        Field.__init__(self,name,default)
        # don't use Wrapper.__init__ because it depends on a single
        # proxy object, not a dict.
        self._proxy=switch
        self._func=func

        self.renameSwitch()

    def renameSwitch(self):
        for key,field in self._proxy.iteritems():
            assert self.debuglevel == 0 or self.dprint("renaming switch %s: from %s to %s" % (str(key),field._name,self._name))
            field._name=self._name
        self._default._name=self._name

    def getProxy(self,obj):
        assert self.debuglevel == 0 or self.dprint("switch obj=%s" % obj)
        val=self._func(obj)
        if val in self._proxy:
            proxy=self._proxy[val]
        else:
            proxy=self._default
        assert self.debuglevel == 0 or self.dprint("switch found proxy=%s" % proxy)
        return proxy
        

class UnpackOnly(Wrapper):
    def __init__(self,proxy):
        Wrapper.__init__(self,proxy)

    def unpack(self,fh,obj):
        Wrapper.unpack(self,fh,obj)

    def pack(self,fh,obj):
        pass

class PackOnly(Wrapper):
    def __init__(self,proxy):
        Wrapper.__init__(self,proxy)

    def unpack(self,fh,obj):
        pass

    def pack(self,fh,obj):
        Wrapper.pack(self,fh,obj)

class Modify(Field):
    def __init__(self,func):
        Field.__init__(self,None)
        self._func=func

    def storeDefault(self,obj):
        return
        
    def getNumBytes(self,obj):
        return 0

    def unpack(self,fh,obj):
        self._func(obj)

    def pack(self,fh,obj):
        self._func(obj)

class ModifyUnpack(Modify):
    def pack(self,fh,obj):
        pass

class ModifyPack(Modify):
    def unpack(self,fh,obj):
        pass


class ComputeUnpack(Field):
    def __init__(self,name,func,default=None):
        Field.__init__(self,name,default)
        self._func=func

    def unpack(self,fh,obj):
        setattr(obj,self._name,self._func(obj))

    def pack(self,fh,obj):
        pass

class ComputePack(Wrapper):
    def __init__(self,proxy,func):
        Wrapper.__init__(self,proxy)
        self._func=func

    # Have to override getNumBytes because the Wrapper version of this
    # method doesn't compute the value.  When the ComputePack is in an
    # If statement, it needs the value to be computed before checking
    # the condition.
    def getNumBytes(self,obj):
        proxy=self.getProxy(obj)
        value=self._func(obj)
        setattr(obj,proxy._name,value)
        return Wrapper.getNumBytes(self,obj)

    def pack(self,fh,obj):
        proxy=self.getProxy(obj)
        value=self._func(obj)
        setattr(obj,proxy._name,value)
        proxy.pack(fh,obj)

class Anchor(ComputeUnpack):
    def __init__(self,name,default=None):
        ComputeUnpack.__init__(self,name,None,default)

    def unpack(self,fh,obj):
        setattr(obj,self._name,fh.tell())

    def pack(self,fh,obj):
        setattr(obj,self._name,fh.tell())

class UBInt32Checksum(ComputeUnpack):
    debuglevel=0
    _fmt = '>%dI'
    
    def __init__(self, name, anchor):
        ComputeUnpack.__init__(self, name, None, 0)
        self._anchor = anchor

    def unpack(self, fh, obj):
        save = fh.tell()
        pos = getattr(obj, self._anchor)
        fh.seek(pos)
        bytes = fh.read(save - pos)
        nums = struct.unpack(self._fmt % (len(bytes)/4), bytes)
        #print nums
        total = reduce(lambda a,b: a+b, nums)
        total = (~total + 1) & 0xffffffff
        setattr(obj, self._name, total)

    def pack(self, fh, obj):
        pass

class ULInt32Checksum(UBInt32Checksum):
    _fmt = '<%dI'

class Pointer(Wrapper):
    def __init__(self,proxy,func):
        Wrapper.__init__(self,proxy)
        self._func=func

    def unpack(self,fh,obj):
        save=fh.tell()
        fh.seek(self._func(obj))
        Wrapper.unpack(self,fh,obj)
        fh.seek(save)

    def pack(self,fh,obj):
        save=fh.tell()
        fh.seek(self._func(obj))
        Wrapper.pack(self,fh,obj)
        fh.seek(save)


class ReadAhead(Wrapper):
    def __init__(self,proxy):
        Wrapper.__init__(self,proxy)

    def getNumBytes(self,obj):
        return 0

    def unpack(self,fh,obj):
        save=fh.tell()
        Wrapper.unpack(self,fh,obj)
        fh.seek(save)

    def pack(self,fh,obj):
        pass


class IfElse(Wrapper):
    def __init__(self,func,ifproxy,elseproxy=None,debug=False):
        Wrapper.__init__(self,ifproxy)
        self._func=func
        if elseproxy is not None:
            self._else=elseproxy
        else:
            self._else=NoOp(self._proxy._name)
        if debug:
            self.debuglevel=1
            self._proxy.debuglevel=1
            self._else.debuglevel=1

    def getProxy(self,obj):
        assert self.debuglevel == 0 or self.dprint("switch obj=%s" % obj)
        val=self._func(obj)
        if val:
            proxy=self._proxy
        else:
            proxy=self._else
        assert self.debuglevel == 0 or self.dprint("switch found proxy=%s" % proxy._name)
        return proxy

class If(IfElse):
    pass

class Adapter(Wrapper):
    def __init__(self,proxy):
        Wrapper.__init__(self,proxy)
        self._initial_offset = 0

    def decode(self,value,obj):
        raise NotImplementedError

    def unpack(self,fh,obj):
        proxy=self.getProxy(obj)
        self._initial_offset = fh.tell()
        proxy.unpack(fh,obj)
        converted=self.decode(getattr(obj,proxy._name),obj)
        setattr(obj,proxy._name,converted)

    def encode(self,value,obj):
        raise NotImplementedError

    def pack(self,fh,obj):
        proxy=self.getProxy(obj)
        save=getattr(obj,proxy._name)
        converted=self.encode(save,obj)
        setattr(obj,proxy._name,converted)
        proxy.pack(fh,obj)
        setattr(obj,proxy._name,save)

class OffsetStringIO(object):
    """Wrapper around StringIO to report the correct offset within the file
    
    When using the MetaSizeList, a StringIO instance is used to decode the
    values, but that means that the file offset will be wrong if an Anchor is
    used within the elements.  This class, and the _initial_offset attribute
    of the adapter, is used to get around that problem.
    """
    def __init__(self, data, offset):
        self.s = StringIO(data)
        self.offset = offset
    
    def __getattr__(self, attr):
        return getattr(self.s, attr)
    
    def tell(self):
        return self.s.tell() + self.offset

class MetaSizeList(Adapter):
    """
    This structure is for when you know the length of the field, but
    you don't know how many elements are in the field.  The elements
    are parsed until the field runs out of bytes.  Upon writing, the
    field length will have to be changed to match the number of
    elements if the number of elements has changed.
    """
    debuglevel=0
        
    def __init__(self,proxy,func):
        Adapter.__init__(self,MetaField(proxy._name,func))
        self._itemproxy=proxy
        #self._debug=True

    # Unpack: call the proxy to get the raw data, then translate to
    # the required user data type
    def decode(self,value,obj):
        proxy=self._itemproxy
        data=[]
        length=len(value)
        assert self.debuglevel == 0 or self.dprint("overall length=%d, obj=%s" % (length,obj))
        fh=OffsetStringIO(value, self._initial_offset)
        i=0
        while fh.tell() < len(value) + self._initial_offset:
            copy=proxy.getCopy(obj)
            setattr(copy,"_",obj)
            assert self.debuglevel == 0 or self.dprint("attempting to read primitive object %s.%s" % (obj.__class__.__name__,proxy._name))
            setattr(copy,"_listindex",i)
            proxy.unpack(fh,copy)
            assert self.debuglevel == 0 or self.dprint("primitive copy=%s" % copy)
            if isinstance(proxy,Record):
                data.append(copy)
            else:
                data.append(getattr(copy,proxy._name))
            i+=1
        return data

    # pack: translate the user data type to the type the proxy can
    # use.  The proxy will then turn it into raw bytes
    def encode(self,value,obj):
        proxy=self._itemproxy
        num=len(value)
        fh=StringIO()
        assert self.debuglevel == 0 or self.dprint("looping %d times for proxy %s" % (num,proxy._name))
        for i in range(num):
            assert self.debuglevel == 0 or self.dprint("value[%d]=%s" % (i,value[i]))
            if isinstance(proxy,Record):
                proxy.pack(fh,value[i])
            else:
                setattr(obj,proxy._name,value[i])
                proxy.pack(fh,obj)
        return fh.getvalue()


class CookedInt(Adapter):
    def __init__(self,proxy,fmt=None):
        Adapter.__init__(self,proxy)

        # Fail hard if the user tries to use a CookedInt adapter with
        # a meta construct by passing None as the value dict.
        if fmt is not None:
            self._fmt=fmt
        else:
            self._fmt="%0"+str(proxy.getNumBytes(None))+"d"

    # Unpack: call the proxy to get the raw data, then translate to
    # the required user data type
    def decode(self,value,obj):
        assert self.debuglevel == 0 or self.dprint("converting %s to int" % value)
        try:
            return int(value)
        except ValueError:
            print "failed converting value='%s'" % str(value)
            print self
            print self._proxy
            return 0

    # pack: translate the user data type to the type the proxy can
    # use.  The proxy will then turn it into raw bytes
    def encode(self,value,obj):
        try:
            return self._fmt % value
        except TypeError:
            print "failed converting %s to %s" % (value,self._fmt)
            print self
            print self.proxy
            raise

class CookedFloat(Adapter):
    def __init__(self,proxy,fmt):
        Adapter.__init__(self,proxy)

        # Fail hard if the user tries to use a CookedInt adapter with
        # a meta construct by passing None as the value dict.
        self._fmt=fmt

    # Unpack: call the proxy to get the raw data, then translate to
    # the required user data type
    def decode(self,value,obj):
        assert self.debuglevel == 0 or self.dprint("converting %s to float" % value)
        try:
            return float(value)
        except ValueError:
            print "failed converting value='%s'" % str(value)
            print self
            print self._proxy
            return 0

    # pack: translate the user data type to the type the proxy can
    # use.  The proxy will then turn it into raw bytes
    def encode(self,value,obj):
        return self._fmt % value

class List(Wrapper):
    def __init__(self,proxy,num):
        Wrapper.__init__(self,proxy)
        self._num=num
        
    def storeDefault(self,obj):
        proxy=self.getProxy(None)
        setattr(obj,proxy._name,[])

    def storeDefault(self,obj):
        proxy=self.getProxy(None)
        data=[]
        num=self.getRepeats(obj)
        assert self.debuglevel == 0 or self.dprint("looping %d times for proxy %s" % (num,proxy._name))
        if isinstance(proxy,Record):
            for i in range(num):
                # call superclass unpack that handles Record subclasses
                assert self.debuglevel == 0 or self.dprint("attempting to read %s.%s" % (obj.__class__.__name__,proxy._name))
                copy=proxy.getCopy(obj)
                setattr(copy,"_",obj)
                setattr(copy,"_listindex",i)
                copy.storeDefault(obj)
                data.append(copy)
        else:
            default = proxy.getDefault(obj)
            for i in range(num):
                data.append(default)
            
        # replace the parent's copy of the proxied object with the new list
        setattr(obj,proxy._name,data)

    def getRepeats(self,obj):
        return self._num

    def getNumBytes(self,obj):
        proxy=self.getProxy(obj)
        # All objects aren't necessarily the same length now
##        setattr(obj,"_listindex",0)
##        return self.getRepeats(obj)*proxy.getNumBytes(obj)
        size=0
        num=self.getRepeats(obj)
        assert self.debuglevel == 0 or self.dprint("looping %s times for proxy %s (type %s)" % (str(num),proxy._name,proxy.__class__.__name__))
        if isinstance(proxy,Record):
            array=getattr(obj,proxy._name)
            for i in range(num):
                # call superclass unpack that handles Record subclasses
                assert self.debuglevel == 0 or self.dprint("attempting to get size %s.%s" % (obj.__class__.__name__,proxy._name))
                #copy=proxy.getCopy(obj)
                assert self.debuglevel == 0 or self.dprint(array[i])
                dup=copy.copy(array[i])
                assert self.debuglevel == 0 or self.dprint(dup)
                setattr(dup,"_",obj)
                setattr(dup,"_listindex",i)
                assert self.debuglevel == 0 or self.dprint("obj = %s\ncopy = %s" % (obj,dup))
                size+=proxy.getNumBytes(dup)
        else:
            dup=proxy.getCopy(obj)
            setattr(dup,"_",obj)
            for i in range(num):
                # call superclass unpack that handles Record subclasses
                assert self.debuglevel == 0 or self.dprint("attempting to get size of primivite object %s.%s" % (obj.__class__.__name__,proxy._name))
                setattr(dup,"_listindex",i)
                size+=Wrapper.getNumBytes(self,dup)
        return size

    def unpack(self,fh,obj):
        proxy=self.getProxy(obj)
        data=[]
        num=self.getRepeats(obj)
        assert self.debuglevel == 0 or self.dprint("looping %d times for proxy %s" % (num,proxy._name))
        if isinstance(proxy,Record):
            for i in range(num):
                # call superclass unpack that handles Record subclasses
                assert self.debuglevel == 0 or self.dprint("attempting to read %s.%s" % (obj.__class__.__name__,proxy._name))
                copy=proxy.getCopy(obj)
                setattr(copy,"_",obj)
                setattr(copy,"_listindex",i)
                proxy.unpack(fh,copy)
                data.append(copy)
        else:
            copy=proxy.getCopy(obj)
            setattr(copy,"_",obj)
            for i in range(num):
                # call superclass unpack that handles Record subclasses
                assert self.debuglevel == 0 or self.dprint("attempting to read primitive object %s.%s" % (obj.__class__.__name__,proxy._name))
                setattr(copy,"_listindex",i)
                Wrapper.unpack(self,fh,copy)
                assert self.debuglevel == 0 or self.dprint("primitive copy=%s" % copy)
                data.append(getattr(copy,proxy._name))
            
            
        # replace the parent's copy of the proxied object with the new list
        setattr(obj,proxy._name,data)

    def pack(self,fh,obj):
        proxy=self.getProxy(obj)
        save=getattr(obj,proxy._name)
        num=self.getRepeats(obj)
        assert self.debuglevel == 0 or self.dprint("looping %d times for proxy %s; save=%s" % (num,proxy._name,save))
        try:
            for i in range(num):
                assert self.debuglevel == 0 or self.dprint("save[%d]=%s" % (i,save[i]))
                if isinstance(proxy,Record):
                    proxy.pack(fh,save[i])
                else:
                    setattr(obj,proxy._name,save[i])
                    proxy.pack(fh,obj)
        except:
            print ("Error processing %s: i=%d save=%s" % (proxy._name, i, str(save)))
            raise
        setattr(obj,proxy._name,save)

class MetaList(List):
    def __init__(self,proxy,func):
        List.__init__(self,proxy,func)
        #self._debug=1

    def storeDefault(self,obj):
        proxy=self.getProxy(None)
        setattr(obj,proxy._name,[])

    def getRepeats(self,obj):
        return self._num(obj)




##### Derived types

def SLInt8(name,default=0): return FormatField(name,'<b',default)
def SBInt8(name,default=0): return FormatField(name,'>b',default)
def ULInt8(name,default=0): return FormatField(name,'<B',default)
def UBInt8(name,default=0): return FormatField(name,'>B',default)
def SLInt16(name,default=0): return FormatField(name,'<h',default)
def SBInt16(name,default=0): return FormatField(name,'>h',default)
def ULInt16(name,default=0): return FormatField(name,'<H',default)
def UBInt16(name,default=0): return FormatField(name,'>H',default)
def SLInt32(name,default=0): return FormatField(name,'<i',default)
def SBInt32(name,default=0): return FormatField(name,'>i',default)
def ULInt32(name,default=0): return FormatField(name,'<I',default)
def UBInt32(name,default=0): return FormatField(name,'>I',default)
def LFloat32(name,default=0): return FormatField(name,'<f',default)
def BFloat32(name,default=0): return FormatField(name,'>f',default)
def LFloat64(name,default=0): return FormatField(name,'<d',default)
def BFloat64(name,default=0): return FormatField(name,'>d',default)

def Tuple(field,num): return List(field,num)

def String(name,length): return MetaField(name,length)


class Record(Field):
    """baseclass for binary records"""
    _defaultstore={}
    
    typedef=()
    
    def __init__(self,name=None,default=None,typedef=None,debuglevel=0):
        if debuglevel>0:
            self.debuglevel=debuglevel
        if name==None: name==self.__class__.__name__
        if typedef is not None:
            if not isinstance(typedef,list) and not isinstance(typedef,tuple):
                typedef=(typedef,)
            self.typedef=typedef
        if self.typedef is None or len(self.typedef)==0:
            raise FieldTypedefError("Missing typedefs for %s %s" % (self.__class__.__name__,name))
            
        Field.__init__(self,name,default)

        self._currentlyprocessing=None
        
        self.storeDefault(self)
    
    def getCopy(self, obj):
        """Deep copy of subrecord
        
        Any Record that uses Records in the typedef needs to be deep copied
        rather than shallow copied as done in Field.  If it is shallow copied,
        the subrecords created by the shallow copy all point to the same
        object.
        """
        #dprint("Deep copy of %s: %s" % (self._name, self))
        template = Field.getCopy(self, obj)
#        return Field.getCopy(self, obj)
        for field in self.typedef:
            if isinstance(field,Record):
                # set temporary reference of subobject to None
                setattr(template,field._name,field.getCopy(obj))
                assert self.debuglevel == 0 or self.dprint("  copy of %s = %s" % (field._name,getattr(obj,field._name)))
                child=getattr(template,field._name)
                # set obj._ to be obj for parent object reference
                assert self.debuglevel == 0 or self.dprint("  child=%s" % child.__class__.__name__)
                setattr(child,"_",template)
                #field.storeDefault(child)
        return template
    
    def storeDefault(self,obj):
        assert self.debuglevel == 0 or self.dprint("storing defaults for %s" % self.__class__.__name__)
        for field in self.typedef:
            self._currentlyprocessing=field
            assert self.debuglevel == 0 or self.dprint("  typedef=%s" % field)
            if isinstance(field,Record):
                # set temporary reference of subobject to None
                setattr(obj,field._name,Field.getCopy(field, obj))
                assert self.debuglevel == 0 or self.dprint("  copy of %s = %s" % (field._name,getattr(obj,field._name)))
                child=getattr(obj,field._name)
                # set obj._ to be obj for parent object reference
                assert self.debuglevel == 0 or self.dprint("  child=%s" % child.__class__.__name__)
                setattr(child,"_",obj)
                #field.storeDefault(child)
            else:
                assert self.debuglevel == 0 or self.dprint("  primitive object %s, store in %s" % (field._name,obj))
                if isinstance(self._default,dict) and field._name in self._default:
                    if isinstance(field,Wrapper):
                        proxy=field.getProxy(obj)
                        proxy._default=self._default[field._name]
                    else:
                        field._default=self._default[field._name]
                field.storeDefault(obj)
            assert self.debuglevel == 0 or self.dprint("  setting %s.%s=%s" % (field.__class__.__name__,field._name,field))
        assert self.debuglevel == 0 or self.dprint("defaults for %s" % (str(obj)))
        self._currentlyprocessing=None


    def getNumBytes(self,obj,subtypedefs=None):
        length=0
        if subtypedefs is not None:
            typedefs=subtypedefs
        else:
            typedefs=self.typedef
        for field in typedefs:
            self._currentlyprocessing=field
            if isinstance(field,Record):
                bytes=field.getNumBytes(getattr(obj,field._name))
                assert self.debuglevel == 0 or self.dprint("%s.getNumBytes(values[%s])=%d" % (str(field),field._name,bytes))
                length+=bytes
            else:
                bytes=field.getNumBytes(obj)
                assert self.debuglevel == 0 or self.dprint("%s.getNumBytes(values[%s])=%d" % (str(field),field._name,bytes))
                length+=bytes
##            length+=field.getNumBytes(obj)
        assert self.debuglevel == 0 or self.dprint("length=%d" % length)
        self._currentlyprocessing=None
        return length
    
    def unpack(self,fh,obj):
        assert self.debuglevel == 0 or self.dprint("fh.tell()=%s before=%s" % (fh.tell(),obj))
        for field in self.typedef:
            self._currentlyprocessing=field
            assert self.debuglevel == 0 or self.dprint("field=%s" % str(field))
            if isinstance(field,Record):
                assert self.debuglevel == 0 or self.dprint("calling %s.unpack(obj.%s)" % (str(field),field._name))
                field.unpack(fh,getattr(obj,field._name))
            else:
                assert self.debuglevel == 0 or self.dprint("field=%s" % str(field))
                field.unpack(fh,obj)
##            field.unpack(fh,obj)
            assert self.debuglevel == 0 or self.dprint("unpacked %s=%s" % (field._name,field._name and getattr(obj,field._name) or "None"))
        assert self.debuglevel == 0 or self.dprint("fh.tell()=%s after=%s" % (fh.tell(),obj))
        self._currentlyprocessing=None

    def pack(self,fh,obj):
        #fh=StringIO()
        for field in self.typedef:
            self._currentlyprocessing=field
            assert self.debuglevel == 0 or self.dprint("field=%s" % str(field))
            if isinstance(field,Record):
                field.pack(fh,getattr(obj,field._name))
            else:
                assert self.debuglevel == 0 or self.dprint("packing %s" % field)
                field.pack(fh,obj)
##            assert self.debuglevel == 0 or self.dprint("packed %s=%s" % (field._name,repr(bytes)))
##            fh.write(bytes)
##        return fh.getvalue()
        self._currentlyprocessing=None
    
    def unserialize(self,fh,partial=False):
        try:
            self.unpack(fh,self)
        except EOFError:
            print "EOFError: failed while processing field %s" % self._currentlyprocessing
            print self
            if not partial:
                raise

        self.unserializePostHook()

    def unserializePostHook(self):
        pass

    def serializePreHook(self):
        pass

    def serialize(self,fh,partial=False):
        self.serializePreHook()
        
        try:
            self.pack(fh,self)
        except struct.error:
            print "struct.error: failed while processing field %s" % self._currentlyprocessing
            print self
            if partial:
                return
            raise

    def size(self):
        return self.getNumBytes(self)

    def sizeSubset(self,start,end):
        typedefs=[]
        i=iter(self.typedef)
        for field in i:
            #print field._name
            if field._name==start:
                assert self.debuglevel == 0 or self.dprint("starting at field=%s" % field._name)
                typedefs.append(field)
                break
        for field in i:
            assert self.debuglevel == 0 or self.dprint("including field=%s" % field._name)
            typedefs.append(field)
            if field._name==end:
                assert self.debuglevel == 0 or self.dprint("stopping at field=%s" % field._name)
                break

        bytes=self.getNumBytes(self,subtypedefs=typedefs)
        assert self.debuglevel == 0 or self.dprint("total length = %s" % bytes)
        return bytes

    def _getString(self,indent=""):
        lines=["%s%s %s:" % (indent,repr(self),self._name)]
        if "_print_all" in self.__dict__ or self.print_all:
            printall = True
        else:
            printall = False
        for field in self.typedef:
            name = field._name
            # ignore all keys that start with an underscore
            if name and not name.startswith("_") and name in self.__dict__:
                value=self.__dict__[name]
                lines.append(repr1(name,value,indent+base_indent, printall))
        if "_" in self.__dict__.keys():
            lines.append("%s_ = %s" % (indent+base_indent,repr(self.__dict__["_"])))
        return "\n".join(lines)
    
    def _getDottedStringPrefix(self, prefix, index=-1):
        if index < 0:
            prefix = "%s.%s" % (prefix, self._name)
        return prefix
    
    def _getDottedString(self, prefix, index=-1):
        lines=[]
        if "_print_all" in self.__dict__ or self.print_all:
            printall = True
        else:
            printall = False
        prefix = self._getDottedStringPrefix(prefix, index)
        for field in self.typedef:
            name = field._name
            # ignore all keys that start with an underscore
            if not name.startswith("_"):
                value=self.__dict__[name]
                if index >= 0:
                    name = "%s[%d]" % (name, index)
                lines.append(repr2(name, value, prefix, printall))
        return "\n".join(lines)
    
    def getTree(self):
        """Get a list of nodes for use in a tree display.
        
        The returned list of nodes is a list of tuples for each field in
        the Record.  Each entry in the tuple will have either two or three
        entries.  If the field is a list, the tuple with have two entries: the
        name and the list of records contained within the field.  If the field
        represents another Record, the tuple will contain the name and the
        Record.  Otherwise, the tuple contains the name, the python value, and
        the packed value.
        """
        items = []
        for field in self.typedef:
            name = field._name
            # ignore all keys that start with an underscore
            if name and not name.startswith("_") and name in self.__dict__:
                if name == "header_end":
                    break
                #dprint("name=%s" % name)
                if isinstance(field,Record):
                    # the typedef holds a blank copy of the record; we want the
                    # actual data instead of the template so we need to use
                    # getattr to get the real record
                    field = getattr(self, name)
                    #dprint("record=%s" % str(field))
                    items.append((name, field))
                else:
                    value = self.__dict__[name]
                    if isinstance(value, list):
                        items.append((name, value))
                    else:
                        fh = StringIO()
                        field.pack(fh, self)
                        items.append((name, value, fh.getvalue()))
                    # It's possible that field.pack has altered the value.
                    # Reset it to the prevous value
                    if value != self.__dict__[name]:
                        #dprint("%s changed from %s to %s. Resetting!" % (name, value, self.__dict__[name]))
                        self.__dict__[name] = value
        return items


class RecordList(list):
    def __init__(self,parent):
        list.__init__(self)
        self.parent=parent
        
    def append(self,item):
        #print "before: current length=%d" % len(self)
        #print "item=%s" % item
        if isinstance(item, Field):
            item._=self.parent
            item._listindex=len(self)
        list.append(self,item)
