import os,sys,re

from peppy.iofilter import *

from tests.mock_wx import getSTC

from nose.tools import *

class TestURLInfo:
    def testHttp(self):
        url=URLInfo("http://www.flipturn.org")
        eq_(url.protocol,'http')
        eq_(url.netloc,'www.flipturn.org')
        url=URLInfo("http://www.flipturn.org/peppy/")
        eq_(url.protocol,'http')
        eq_(url.netloc,'www.flipturn.org')
        eq_(url.path,'/peppy/')
        url=URLInfo("http://www.flipturn.org/peppy/index.html")
        eq_(url.protocol,'http')
        eq_(url.netloc,'www.flipturn.org')
        eq_(url.path,'/peppy/index.html')
        url=URLInfo("http://www.flipturn.org/peppy/index.html?extra_stuff")
        eq_(url.protocol,'http')
        eq_(url.netloc,'www.flipturn.org')
        eq_(url.path,'/peppy/index.html')
        eq_(url.query_string,'extra_stuff')
        
    def testFile(self):
        url=URLInfo("file:///etc/profile", usewin=False)
        eq_(url.protocol,'file')
        eq_(url.url,'file:///etc/profile')
        url=URLInfo("file:README.txt", usewin=False)
        eq_(url.protocol,'file')
        eq_(os.path.basename(url.path),'README.txt')
        url=URLInfo("file://README.txt", usewin=False)
        eq_(url.protocol,'file')
        eq_(os.path.basename(url.path),'README.txt')
        url=URLInfo("README.txt", usewin=False)
        eq_(url.protocol,'file')
        eq_(os.path.basename(url.path),'README.txt')
        
    def testWindowsFile(self):
        url=URLInfo("c:/path/to/some/file.txt",usewin=True)
        eq_(url.protocol,'file')
        eq_(url.url,'file:///c:/path/to/some/file.txt')
        url=URLInfo("file://c:/path/to/some/file.txt",usewin=True)
        eq_(url.protocol,'file')
        eq_(url.url,'file:///c:/path/to/some/file.txt')
        url=URLInfo("file:c:/path/to/some/file.txt",usewin=True)
        eq_(url.protocol,'file')
        eq_(url.url,'file:///c:/path/to/some/file.txt')
        url=URLInfo("file:///c:/path/to/some/file.txt",usewin=True)
        eq_(url.protocol,'file')
        eq_(url.url,'file:///c:/path/to/some/file.txt')
        
    def testAbout(self):
        url=URLInfo("about:authors")
        eq_(url.protocol,"about")
        eq_(url.path,"authors")

    def testFileRelative(self):
        urlinfo = URLInfo("file://LICENSE")
        cwd = os.getcwd()
        eq_(urlinfo.url, "file:///%s" % os.path.join(cwd, 'LICENSE').replace('\\','/').lstrip('/'))
        eq_(urlinfo.protocol,'file')
        print urlinfo
        eq_(os.path.basename(urlinfo.path),'LICENSE')

class TestGetReader:
    def testFile(self):
        url = URLInfo("file:LICENSE")
        fh = url.getReader()
        cwd = os.getcwd()
        eq_(url.url, "file:///%s" % os.path.join(cwd, 'LICENSE').replace('\\','/').lstrip('/'))
        eq_(url.protocol,'file')
        eq_(os.path.basename(url.path),'LICENSE')
        stc=getSTC()
        stc.readFrom(fh)
        text=stc.GetText()
        eq_(text[0:32],'\t\t    GNU GENERAL PUBLIC LICENSE')
        
    def testFileRelative(self):
        url = URLInfo("file:LICENSE")
        fh = url.getReader()
        cwd = os.getcwd()
        eq_(url.url, "file:///%s" % os.path.join(cwd, 'LICENSE').replace('\\','/').lstrip('/'))
        eq_(url.protocol,'file')
        print url
        eq_(os.path.basename(url.path),'LICENSE')
        stc=getSTC()
        stc.readFrom(fh)
        text=stc.GetText()
        eq_(text[0:32],'\t\t    GNU GENERAL PUBLIC LICENSE')
        
    def testFileDefault(self):
        url = URLInfo("file:LICENSE")
        fh = url.getReader()
        cwd = os.getcwd()
        eq_(url.url, "file:///%s" % os.path.join(cwd, 'LICENSE').replace('\\','/').lstrip('/'))
        eq_(url.protocol,'file')
        eq_(os.path.basename(url.path),'LICENSE')
        stc=getSTC()
        stc.readFrom(fh)
        text=stc.GetText()
        eq_(text[0:32],'\t\t    GNU GENERAL PUBLIC LICENSE')
        
    def testChatbots(self):
        import peppy.plugins.shell_mode
        import peppy.plugins.chatbots
        URLHandler.clearHandlers()
        url = URLInfo("shell:eliza")
        eq_(url.url, "shell:eliza")
        eq_(url.protocol,'shell')
        eq_(url.path,'eliza')

##    def testWindowsFile(self):
##        fh=GetReader("file://c:/some/path.txt",usewin=True)
##        #eq_(url.url, "file:/c:/some/path.txt")
##        eq_(url.protocol,'file')
##        eq_(url.path,'c:/some/path.txt')
##        fh=GetReader("c:/some/path.txt",usewin=True)
##        eq_(url.protocol,'file')
##        eq_(url.path,'c:/some/path.txt')
        
