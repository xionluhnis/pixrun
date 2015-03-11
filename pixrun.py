#!/usr/bin/env python
##########################################################################
#
# Author: Alexandre Kaspar <akaspar@mit.edu>
# Date: March 2015
# Released under the MIT License
#
##########################################################################


"""Entry point for PIXrun parser"""

import sys
from pixparser import Parser, Verbosity

def main():
    if len(sys.argv) < 2:
        sys.stdout.flush()
        sys.stderr.write('Requires a pixfile as argument!\n')
        exit(1)
    else:
        
        pixfile = open(sys.argv[1], 'rb')
        verbosity = Verbosity.silent
        if len(sys.argv) >= 3:
            verbosity = sys.argv[2]
        # create parser and run it
        parser = Parser(pixfile, verbosity)
        parser.parse()


if __name__ == '__main__':
    main()
