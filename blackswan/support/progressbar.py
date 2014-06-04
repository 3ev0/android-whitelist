__author__ = 'ivo'

import sys
import os
import math

class Progressbar(object):
    '''
    Represents a simple progressbar.
    Works only on linux systems.
    '''
    def __init__(self, total, description, unit="MB", outstream=sys.stdout):
        '''
        Constructor
        '''
        self.total = total
        self.cur = 0
        self.stream = outstream
        self.stream.write(description + "\n")
        self.unit = unit

        (rows, columns) = os.popen('stty size', 'r').read().split()
        self.width = int(columns) - len(self.unit) - 25
        self.termwidth = int(columns)
        self.refresh()
        return

    def update(self, amount, diff=True):
        if diff:
            self.cur += amount
        else:
            self.cur = amount
        self.refresh()
        return

    def refresh(self):
        try:
            prcnt = math.floor(self.cur/self.total * 100)
        except ZeroDivisionError:
            prcnt = 100
        if self.width < 0:
            prstr = "{:d}%".format(prcnt)
        else:
            fillwidth = round(prcnt/100 * self.width)
            prstr = "[" + ("#"*fillwidth).ljust(self.width,"_") + "]" + " {:d}%".format(prcnt) + "({:d} / {:d} {})".format(self.cur, self.total, self.unit)
        self.stream.write("\r" + prstr.ljust(self.termwidth-1))
        #self.stream.write("\r{:d}%".format(round(self.cur/self.total)))
        return

    def finish(self):
        if self.width > 0:
            prstr = "[" + "#"*self.width + "]" + " 100% done!"
        else:
            prstr = "100% done!\n"
        self.stream.write("\r" + prstr.ljust(self.termwidth-1) + "\n")
        self.stream.flush()
        return