#!/usr/bin/env python
##########################################################################
#
# Author: Alexandre Kaspar <akaspar@mit.edu>
# Date: March 2015
# Released under the MIT License
#
##########################################################################


"""Entry point for PIXrun frame grep program"""

import os
import re
import struct
import sys
from pixparser import Parser, Verbosity

LongSize = 2 * struct.calcsize('I')

class FrameMatcher(Parser):
    def __init__(self, stream, pattern, verbosity):
        Parser.__init__(self, stream, 0)
        self.verb = int(verbosity)
        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.frames = {}
        self.strbuffer = ''
        self.lastFrame = -1

    def flush(self):
        if self.lastFrame is -1:
            return
        print "Frame #%i (%i)%s" % (self.lastFrame, self.frames[self.lastFrame], self.strbuffer)
        self.strbuffer = ''

    def matched(self, functionName):
        frame = self.frameID - 1
        if self.lastFrame is not frame:
            self.flush()
            self.lastFrame = frame

        if frame not in self.frames:
            self.frames[frame] = 1
        else:
            self.frames[frame] += 1

        if self.verb > Verbosity.silent:
            self.strbuffer = "%s\n\t%s @ %i" % (self.strbuffer, functionName, self.chunkID - 1)

    def processCall(self, functionName):
        if self.verb > Verbosity.basic:
            print "%s -> %s" % (self.pattern, functionName)
        m = re.search(self.pattern, functionName)
        if m is not None:
            self.matched(functionName)

    def processFrame(self, eventType, data, offsets):
        return True


def main():
    if len(sys.argv) < 3:
        sys.stdout.flush()
        sys.stderr.write('Usage: grep_frames.py pix_in pattern\n')
        exit(1)
    else:
        stream = open(sys.argv[1], 'rb')
        pattern = sys.argv[2]
        verbosity = Verbosity.silent
        if len(sys.argv) >= 4:
            verbosity = sys.argv[3]
        parser = FrameMatcher(stream, pattern, verbosity)
        parser.parse()
        parser.flush()

if __name__ == '__main__':
    main()
