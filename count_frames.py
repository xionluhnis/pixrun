#!/usr/bin/env python
##########################################################################
#
# Author: Alexandre Kaspar <akaspar@mit.edu>
# Date: March 2015
# Released under the MIT License
#
##########################################################################


"""Entry point for PIXrun frame counter"""

import sys
from pixparser import Parser

class FrameParser(Parser):
    def __init__(self, stream):
        Parser.__init__(self, stream, 0)
        self.count = 0

    def parseFrame(self, data, offsets):
        self.count += 1

def main():
    if len(sys.argv) < 2:
        sys.stdout.flush()
        sys.stderr.write('Requires a pixfile as argument!\n')
        exit(1)
    else:
        
        pixfile = open(sys.argv[1], 'rb')
        parser = FrameParser(pixfile)
        parser.parse()
        print '#frames = %i\n' % parser.count

if __name__ == '__main__':
    main()
