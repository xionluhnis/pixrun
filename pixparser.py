#!/usr/bin/env python
##########################################################################
#
# Modification by Alexandre Kaspar <akaspar@mit.edu>
# Date: March 2015
# Released under the MIT License
#
### Original license #####################################################
# 
# Copyright 2012 Jose Fonseca
# All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
##########################################################################/


"""Parser for PIXRun files."""


import os
import struct
import sys
from pixfunc import functionName

class Verbosity:
    silent  = 0
    minimal = 1
    basic   = 2
    verbose = 3
    alldata = 4

class Logger:

    def __init__(self, verbosity):
        self.verbosity = int(verbosity)

    def log_minimal(self, str):
        if self.verbosity >= Verbosity.minimal:
            print str

    def log_basic(self, str):
        if self.verbosity >= Verbosity.basic:
            print str

    def log_verbose(self, str):
        if self.verbosity >= Verbosity.verbose:
            print str

    def log_alldata(self, str):
        if self.verbosity >= Verbosity.alldata:
            print str

    def error(self, str):
        std.stdout.flush()
        sys.stderr.write('Error: %s' % str)

class Element:

    def __init__(self, typeId, name, fmt):
        self.typeId = typeId
        self.name = name
        self.fmt = fmt

    def __str__(self):
        return self.name


class EventType:

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def __str__(self):
        s = '%s(%r)' % (self.name, self.fields)
        return s

class Parser(Logger):

    def __init__(self, stream, verbosity=0):
        Logger.__init__(self, verbosity)
        self.stream = stream
        self.lastChunkOffset = 0
        self.nextChunkOffset = 0
        self.elements = {}
        self.eventTypes = {}
        self.chunkID = 1
        self.frameID = 1

    def parse(self):
        while self.parseChunk():
            pass

    def parseChunk(self):
        lastOffset = self.stream.tell()
        self.lastChunkOffset = self.nextChunkOffset

        if lastOffset != self.nextChunkOffset:
            if self.verbosity >= Verbosity.verbose:
                print '%08x: skipping %i bytes' % (lastOffset, self.nextChunkOffset - lastOffset)
                self.parseUnknown()
            self.stream.seek(self.nextChunkOffset)

        # parsing new chunk
        size = self.stream.read(4)
        if not size:
            return False
        size, = struct.unpack('I', size)
        self.nextChunkOffset += 4 + size

        self.log_basic('Chunk %i' % self.chunkID)
        self.chunkID += 1
        self.log_verbose('%08x -> %08x' % (self.lastChunkOffset, self.nextChunkOffset))

        tag = self.parseDWord()
        if tag == 1000:
            self.log_basic('Header')
            self.parseHeader()
        elif tag == 1001:
            self.log_basic('Elem Declare')
            self.parseElementDeclaration()
        elif tag == 1002:
            self.log_basic('Event Type')
            self.parseEventType()
        elif tag == 1003:
            self.log_minimal('Event')
            self.parseEvent()
        elif tag == 1004:
            self.log_basic('Event Async')
            self.parseEventAsync()
        elif tag == 1005:
            self.log_basic('Object Info')
            self.parseObjectInfo()
        elif tag == 1006:
            self.log_basic('System Info')
            self.parseSystemInfo()
        elif tag == 1007:
            self.log_basic('Display Info')
            self.parseDisplayInfo()
        elif tag == 1008:
            self.log_basic('Module Info')
            self.parseModuleInfo()
        else:
            self.log_minimal('%08x: unknown tag %i' % (self.lastChunkOffset, tag))

        return True

    def parseHeader(self):
        unknown1 = self.parseDWord()
        unknown2 = self.parseDWord()
        unknown3 = self.parseDWord()
        unknown4 = self.parseDWord()
        if self.verbosity >= Verbosity.basic:
            print "\tunknown1 = %s" % unknown1
            print "\tunknown2 = %s" % unknown2
            print "\tunknown3 = %s" % unknown3
            print "\tunknown4 = %s" % unknown4

    def parseObjectInfo(self):
        unknown1 = self.parseDWord()
        self.log_basic("\tunknown1 = %s" % unknown1)
        size = self.parseDWord()
        n = 20
        self.log_basic("     Address  ?    ? Creator      ?     Size Pool     Format WidthHeight Depth Mips ?   ?   ?   ?   ?   ?   ?   ?")
        for i in range(0, size / (n*4)):
            attrs = {}
            attrs["Address"] = self.parseDWord()
            attrs["unknown2"] = self.parseDWord()
            attrs["unknown3"] = self.parseDWord()
            attrs["Creator"] = self.parseDWord() # 0: app, 1: runtime
            attrs["unknown5"] = self.parseDWord()
            attrs["Size"] = self.parseDWord()
            attrs["Pool"] = self.parseDWord()
            attrs["Format"] = self.parseDWord()
            attrs["Width"] = self.parseDWord()
            attrs["Height"] = self.parseDWord()
            attrs["Depth"] = self.parseDWord()
            attrs["Mips"] = self.parseDWord()
            attrs["unknown13"] = self.parseDWord()
            attrs["unknown14"] = self.parseDWord()
            attrs["unknown15"] = self.parseDWord()
            attrs["unknown16"] = self.parseDWord()
            attrs["CreateEID"] = self.parseDWord()
            attrs["DestroyEID"] = self.parseDWord()
            attrs["unknown19"] = self.parseDWord()
            attrs["unknown20"] = self.parseDWord()
            self.log_basic("{Address:#010x} {unknown2:d} {unknown3:4d} {Creator:d} {unknown5:#010x} {Size:8d} {Pool:4d} {Format:#010x} {Width:5d} {Height:5d} {Depth:5d} {Mips:2d} {unknown13:3d} {unknown14:3d} {unknown15:3d} {unknown16:3d} {CreateEID:3d} {DestroyEID:3d} {unknown19:3d} {unknown20:3d}".format(**attrs))
        #unknown3 = self.parseDWord()
        #print "\tunknown3 = %s" % unknown3
        unknown4 = self.parseString()
        unknown4 = unknown4.split('\0')
        self.log_basic("\tunknown4 = %r" % unknown4)

    def parseSystemInfo(self):
        unknown1 = self.parseDWord()
        self.log_basic("\tunknown1 = %s" % unknown1)
        winVer = self.parseString()
        self.log_basic("\twinVer = %s" % winVer)
        procDesc = self.parseString()
        self.log_basic("\tprocDesc = %s" % procDesc)

    def parseDisplayInfo(self):
        unknown1 = self.parseDWord()
        self.log_basic("\tunknown1 = %s" % unknown1)
        display = self.parseString()
        self.log_basic("\tdisplay = %s" % display)
        driver = self.parseString()
        self.log_basic("\tdriver = %s" % driver)
        unknown = self.parseString()
        self.log_basic("\tunknown = %s" % unknown)
        unknown = self.parseString()
        self.log_basic("\tunknown = %s" % unknown)
        unknown = self.parseString()
        self.log_basic("\tunknown = %s" % unknown)

    def parseModuleInfo(self):
        unknown1 = self.parseDWord()
        self.log_basic("\tunknown1 = %s" % unknown1)
        numModules = self.parseDWord()
        for i in range(numModules):
            module = self.parseString()
            version = self.parseString()
            self.log_basic("\t%s\t%s" % (module, version))

    def parseUnknown(self):
        if self.verbosity < Verbosity.alldata:
            return
        while self.stream.tell() < self.nextChunkOffset:
            data = self.stream.read(4)
            if len(data) < 4:
                break
            dword, = struct.unpack('I', data)
            print ("\t0x%08x\t%r" % (dword, data))

    def parseElementDeclaration(self):
        elementId = self.parseDWord()
        typeId = self.parseDWord()
        unknown2 = self.parseDWord()
        name = self.parseString()
        fmt = self.parseString()

        if self.verbosity >= Verbosity.basic:
            print 'Element %i' % elementId
            print "\ttypeId = %s" % typeId
            print "\tunknown2 = %s" % unknown2
            print "\tname = %s" % name
            print "\tformat = %s" % fmt

        self.elements[elementId] = Element(typeId, name, fmt)

    def parseEventType(self):
        eventTypeId = self.parseDWord()
        boo = self.parseDWord()
        name = self.parseString()
        self.log_basic('EventType %i / %i' % (eventTypeId, boo))
        self.log_basic("\t%s" % name)
        n = self.parseDWord()
        fields = []
        for i in range(n):
            elementId = self.parseDWord()
            element = self.elements[elementId]
            fieldFormat = self.parseString()
            fields.append((elementId, fieldFormat))
            self.log_basic("\t%s\t%s" % (element, fieldFormat))
        eventType = EventType(name, fields)
        self.eventTypes[eventTypeId] = eventType

    def parseEvent(self):
        eventTypeId = self.parseDWord()
        eventType = self.eventTypes[eventTypeId]

        self.log_minimal("\ttype = %s" % eventType.name)

        # unread the eventTypeId
        self.stream.seek(-4, 1)
        pos = self.stream.tell()

        if eventType.name == "Frame Begin":
            self.log_minimal("\tframe = %i (at %i)" % (self.frameID, pos))

        data = {}
        offsets = {}

        for elementId, fieldFormat in eventType.fields:
            element = self.elements[elementId]
            if fieldFormat.startswith('('):
                off = self.stream.tell()
                value = self.parseElement(element)
                data[element.name] = value
                offsets[element.name] = off
                self.log_basic("\t%s\t%r" % (element.name, value))
                if value is None:
                    break
            else:
                value = fieldFormat
                self.log_verbose("\t%s\t%s" % (element.name, value))

        # for real parsers
        if eventType.name == "Frame Begin":
            selected = self.processFrame(eventType, data, offsets)
            self.frameID += 1
            if self.verbosity < Verbosity.basic and not selected:
                self.nextChunkOffset = data['NextSiblingPos']
                # special case for end of file
                if self.nextChunkOffset == 0:
                    self.nextChunkOffset = os.fstat(self.stream.fileno()).st_size
        else:
            self.processEvent(eventType, data, offsets)

    def processEvent(self, eventType, data, offsets):
        pass # to be implemented by parents

    def processFrame(self, eventType, data, offsets):
        return False # to be implemented by parents

    def parseEventAsync(self):
        eventId = self.parseDWord()
        elementId = self.parseDWord()
        element = self.elements.get(elementId)
        self.log_basic('Event %i Async' % eventId)
        self.log_basic("\telement = %s" % self.elements.get(elementId))
        value = self.parseElement(element)
        if value is not None:
            self.log_alldata("\tvalue = %s" % value)

    def parseElement(self, element):
        if element.typeId == 1:
            return self.parseString()
        elif element.typeId == 2:
            # 32bit hex
            return self.parseDWord()
        elif element.typeId == 3:
            # 32bit int
            return self.parseDWord()
        elif element.typeId == 5:
            # 64bit
            value = self.parseDWord()
            value = value | (self.parseDWord() << 32)
            return value
        elif element.typeId == 7:
            # call package
            size = self.parseDWord()
            self.log_basic("\tsize = %u" % size)
            functionId = self.parseDWord()
            self.log_basic("\tfunction = %s (%i)" % (functionName.get(functionId, ''), functionId))

            if self.verbosity < Verbosity.alldata:
                return None

            for i in xrange(4, size, 4):
                if self.stream.tell() >= self.nextChunkOffset:
                    print "unexpected end of chunk"
                dword = self.parseDWord()
                print ("\t0x%08x" % (dword,))
        else:
            self.error('%s has unknown type %i, %s\n' % (element.name, element.typeId, element.fmt))
            return None

    def parseSetTextureStage(self):
        self.log_basic("\t0x%08x" % self.parseDWord())
        self.log_basic("\t0x%08x" % self.parseDWord())
        self.log_basic("\t0x%08x" % self.parseDWord())

    def parseString(self):
        length = self.parseDWord()
        size = (length + 1) * 2
        buf = self.stream.read(size)
        buf = buf[:length * 2]
        return buf.decode('UTF-16', 'ignore')

    def parseDWord(self):
        dword, = self.parseStruct('I')
        return dword

    def parseStruct(self, fmt):
        size = struct.calcsize(fmt)
        buf = self.stream.read(size)
        return struct.unpack(fmt, buf)


