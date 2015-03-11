#!/usr/bin/env python
##########################################################################
#
# Author: Alexandre Kaspar <akaspar@mit.edu>
# Date: March 2015
# Released under the MIT License
#
##########################################################################


"""Entry point for PIXrun frame copy program"""

import os
import struct
import sys
from pixparser import Parser

LongSize = 2 * struct.calcsize('I')

class FrameParser(Parser):
    def __init__(self, stream, output, frames):
        Parser.__init__(self, stream, 0)
        self.output = output
        self.frames = frames
        self.skipped_bytes  = 0 # byte offset
        self.skipped_events = 0 # EID offset
        self.stream_length = os.fstat(self.stream.fileno()).st_size
        self.parentFrame = 0

    def parse(self):
        Parser.parse(self)
        self.output.flush()

    def parseChunk(self):
        currChunk = self.chunkID
        currFrame = self.frameID
        res = Parser.parseChunk(self)
        
        # did we parse something else than a frame?
        if self.frameID == currFrame:
            print "Copying chunk %i" % currChunk
            # we must copy the chunk
            tempOffset = self.stream.tell() # save 
            self.stream.seek(self.lastChunkOffset)
            buf = self.stream.read(self.nextChunkOffset - self.lastChunkOffset)
            self.output.write(buf)
            # rewind to where we were locally
            self.stream.seek(tempOffset)

        # forward the parsing result
        return res

    def processEvent(self, eventType, data, offsets):
        pass # we could update the EID data

    def processFrame(self, eventType, data, offsets):
        baseOffset = data['ThisEventPos']
        assert baseOffset == self.lastChunkOffset # are our offsets correct?
        nextOffset = data['NextSiblingPos']
        if nextOffset == 0:
            nextOffset = self.stream_length
        
        if str(self.frameID) in self.frames:
            # copy frame:
            print "Copying frame %i" % self.frameID

            # transformed data
            transform = {}
            transform['ThisEventPos'] = baseOffset - self.skipped_bytes
            transform['NextSiblingPos'] = max(0, data['NextSiblingPos'] - self.skipped_bytes)

            self.copyEvent(eventType, data, offsets, transform)
            
            # - copy full frame content
            buf = self.stream.read(nextOffset - self.stream.tell())
            self.output.write(buf)
            
        else:
            # skip frame
	    frameSize = nextOffset - baseOffset
            self.skipped_bytes += frameSize
            print "Skipping frame %i" % self.frameID
        
        return False

    def copyEvent(self, eventType, data, offsets, transform):
        anchor = self.lastChunkOffset # where to copy from
        tempOffset = self.stream.tell()
        for elementId, fieldFormat in eventType.fields:
            element = self.elements[elementId]
            if element.name in transform:
                # copy part up to here
                bufSize = offsets[element.name] - anchor
                if bufSize > 0:
                    self.stream.seek(anchor)
                    buf = self.stream.read(bufSize)
                    self.output.write(buf)
                else:
                    assert bufSize == 0
                # re-parse element data (for size)
                self.parseElement(element)

                # reset anchor
                anchor = self.stream.tell()
                
                # write new element data
                self.writeElement(element, transform[element.name])

        # write the rest up to the next event
        buf = self.stream.read(self.nextChunkOffset - anchor)
        self.output.write(buf)

    def writeElement(self, element, value): # this should keep the same exact buffer size as read data
        if element.typeId == 1:
            self.error('Unsupported string type')
        elif element.typeId == 2:
            self.writeDWord(value) # 32bit hex
        elif element.typeId == 3:
            self.writeDWord(value) # 32bit int
        elif element.typeId == 5:
            self.writeLong(value) # 64bit long
        elif element.typeId == 7:
            self.error('Unsupported call package type')
        else:
            self.error('%s has unknown type %i, %s ... cannot write!\n' % (element.name, element.typeId, element.fmt))

    def writeLong(self, longValue):
        self.writeDWord(longValue & 0xFFFFFFFF)         # first 32 bits
        self.writeDWord((longValue >> 32) & 0xFFFFFFFF) # last 32 bits

    def writeDWord(self, word):
        buf = struct.pack('I', int(word))
        self.output.write(buf)

def main():
    if len(sys.argv) < 4:
        sys.stdout.flush()
        sys.stderr.write('Usage: copy_frames.py pix_in pix_out frame_ranges...\n')
        sys.stderr.write('\n\tpix_in\tinput pix file')
        sys.stderr.write('\n\tpix_out\toutput pix file')
        sys.stderr.write('\n\tranges...\tranges of the form x y,z a:b a:b:c\n\n')
        exit(1)
    else:
        
        stream = open(sys.argv[1], 'rb')
        output = open(sys.argv[2], 'wb')

        # parse frame list
        ranges = ','.join(sys.argv[2:]).replace(' ', ',').split(',')
        frames = {}
        for r in ranges:
            if ':' in r:
                parts = r.split(':')
                start = int(parts[0])
                if len(parts) == 2:
                    step = 1
                    end = int(parts[1]) + 1
                elif len(parts) == 3:
                    step = int(parts[1])
                    end = int(parts[2]) + 1 # we don't support negative steps
                else:
                    sys.stderr.write("Invalid range: %s\n" % r)
                    exit(1)
                for i in range(start, end, step):
                    frames[str(i)] = True
            else:
                frames[r] = True
        
        parser = FrameParser(stream, output, frames)
        parser.parse()

if __name__ == '__main__':
    main()
