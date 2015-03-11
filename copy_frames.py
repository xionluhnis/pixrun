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
        self.skipped = 0 # to be removed from offsets
        self.stream_length = os.fstat(self.stream.fileno()).st_size

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

    def parseFrame(self, data, offsets):
        baseOffset = data['ThisEventPos']
        assert baseOffset == self.lastChunkOffset # are our offsets correct?
        nextOffset = data['NextSiblingPos']
        if nextOffset == 0:
            nextOffset = self.stream_length
        frameSize = nextOffset - baseOffset
        
        if str(self.frameID) in self.frames:
            # copy frame:
            print "Copying frame %i" % self.frameID
            
            # - first up to ThisEventPos
            self.stream.seek(baseOffset)
            buf = self.stream.read(offsets['ThisEventPos'] - baseOffset)
            self.output.write(buf)
            
            # - then ThisEventPos
            self.writeLong(baseOffset - self.skipped)
            
            # - then NextSiblingPos
            postOffset = max(0, data['NextSiblingPos'] - self.skipped)
            self.writeLong(postOffset - self.skipped)
            
            # - finally up to the next frame
            restartOffset = offsets['NextSiblingPos'] + LongSize
            assert restartOffset == offsets['ThisEventPos'] + 2 * LongSize
            self.stream.seek(restartOffset)
            buf = self.stream.read(nextOffset - restartOffset)
            self.output.write(buf)
            
        else:
            # skip frame
            self.skipped += frameSize
            print "Skipping frame %i" % self.frameID

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
