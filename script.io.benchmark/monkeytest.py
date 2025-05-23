#   Copyright (C) 2025 Lunatixz, thodnev
#
#
# This file is part of I/O Benchmark.
# The MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''
Adapted from https://github.com/thodnev/MonkeyTest
I/O Benchmark -- test your hard drive read-write speed in Python
A simplistic script to show that such system programming
tasks are possible and convenient to be solved in Python

I haven't done any command-line arguments parsing, so
you should configure it using the constants below.

The file is being created, then Wrote with random data, randomly read
and deleted, so the script doesn't waste your drive

(!) Be sure, that the file you point to is not smthng
    you need, cause it'll be overWrote during test

Runs on both Python3 and 2, despite that I prefer 3
Has been tested on 3.5 and 2.7 under ArchLinux
'''
#!/usr/bin/env python
'''
MonkeyTest -- test your hard drive read-write speed in Python
A simplistic script to show that such system programming
tasks are possible and convenient to be solved in Python

The file is being created, then written with random data, randomly read
and deleted, so the script doesn't waste your drive

(!) Be sure, that the file you point to is not something
    you need, cause it'll be overwritten during test

Runs on both Python3 and 2, despite that I prefer 3
Has been tested on 3.5 and 2.7 under ArchLinux
Has been tested on 3.5.2 under Ubuntu Xenial
'''
import os, sys
from random import shuffle
import json

ASCIIART = r'''Brought to you by coding monkeys.
Eat bananas, drink coffee & enjoy!
                 _
               ,//)
               ) /
              / /
        _,^^,/ /
       (G,66<_/
       _/\_,_)    _
      / _    \  ,' )
     / /"\    \/  ,_\
  __(,/   >  e ) / (_\.oO
  \_ /   (   -,_/    \_/
    U     \_, _)
           (  /
            >/
           (.oO
'''
# ASCII-art: used part of text-image @ http://www.ascii-art.de/ascii/mno/monkey.txt
# it seems that its original author is Mic Barendsz (mic aka miK)
# text-image is a bit old (1999) so I couldn't find a way to communicate with author
# if You're reading this and You're an author -- feel free to write me

from kodi_six   import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

# Plugin Info
ADDON_ID       = 'script.io.benchmark'
REAL_SETTINGS  = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME     = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION  = REAL_SETTINGS.getAddonInfo('version')

try:  # if Python >= 3.3 use new high-res counter
    from time import perf_counter as time
except ImportError:  # else select highest available resolution counter
    if sys.platform[:3] == 'win':
        from time import clock as time
    else:
        from time import time

class Benchmark:

    def __init__(self, file,write_mb, write_block_kb, read_block_b):
        self.file = file
        self.write_mb = write_mb
        self.write_block_kb = write_block_kb
        self.read_block_b = read_block_b
        wr_blocks = int(self.write_mb * 1024 / self.write_block_kb)
        rd_blocks = int(self.write_mb * 1024 * 1024 / self.read_block_b)
        self.write_results = self.write_test( 1024 * self.write_block_kb, wr_blocks)
        self.read_results = self.read_test(self.read_block_b, rd_blocks)

    def progressDialog(self, percent=0, control=None, message='', header=ADDON_NAME):
        if control is None and int(percent) == 0:
            control = xbmcgui.DialogProgress()
            control.create(header, message)  
        elif control:
            if   int(percent) == 100 or control.iscanceled(): return control.close()
            elif hasattr(control, 'update'): control.update(int(percent), message)
        return control
        
    def write_test(self, block_size, blocks_count, show_progress=True):
        '''
        Tests write speed by writing random blocks, at total quantity
        of blocks_count, each at size of block_size bytes to disk.
        Function returns a list of write times in sec of each block.
        '''
        f = os.open(self.file, os.O_CREAT | os.O_WRONLY, 0o777)  # low-level I/O
        took = []
        if show_progress: prog = self.progressDialog(message=f'Writing: {block_size}')
        else:             prog = None
        for i in range(blocks_count):
            if prog:
                prnt = (i + 1) * 100 / blocks_count
                prog = self.progressDialog(prnt,prog,'Writing: {:.2f} %'.format(prnt))
            buff = os.urandom(block_size)
            start = time()
            os.write(f, buff)
            os.fsync(f)  # force write to disk
            t = time() - start
            took.append(t)

        os.close(f)
        return took

    def read_test(self, block_size, blocks_count, show_progress=True):
        '''
        Performs read speed test by reading random offset blocks from
        file, at maximum of blocks_count, each at size of block_size
        bytes until the End Of File reached.
        Returns a list of read times in sec of each block.
        '''
        f = os.open(self.file, os.O_RDONLY, 0o777)  # low-level I/O
        # generate random read positions
        offsets = list(range(0, blocks_count * block_size, block_size))
        shuffle(offsets)

        took = []
        if show_progress: prog = self.progressDialog(message=f'Reading: {block_size}')
        else:             prog = None
        for i, offset in enumerate(offsets, 1):
            prog = self.progressDialog((i+1/blocks_count),prog,f'Read {i+1}')
            if prog and i % int(self.write_block_kb * 1024 / self.read_block_b) == 0:
                prnt = (i + 1) * 100 / blocks_count
                prog = self.progressDialog(prnt,prog,'rReading: {:.2f} %'.format(prnt))
            start = time()
            os.lseek(f, offset, os.SEEK_SET)  # set position
            buff = os.read(f, block_size)  # read from position
            t = time() - start
            if not buff: break  # if EOF reached
            took.append(t)

        os.close(f)
        return took

    def print_result(self):
        result = ('File {}\n\nWrote {} MB in {:.4f}s\nWrite speed is  {:.2f} MB/s'
                  '\n  max: {max:.2f}, min: {min:.2f}\n'.format(
            self.file.rsplit('userdata', 1)[1], self.write_mb, sum(self.write_results), self.write_mb / sum(self.write_results),
            max=self.write_block_kb / (1024 * min(self.write_results)),
            min=self.write_block_kb / (1024 * max(self.write_results))))
        result += ('\nRead {} x {} B blocks in {:.4f}s\nRead speed is  {:.2f} MB/s'
                   '\n  max: {max:.2f}, min: {min:.2f}\n'.format(
            len(self.read_results), self.read_block_b,
            sum(self.read_results), self.write_mb / sum(self.read_results),
            max=self.read_block_b / (1024 * 1024 * min(self.read_results)),
            min=self.read_block_b / (1024 * 1024 * max(self.read_results))))
        return result


    def get_json_result(self,output_file):
        results_json = {}
        results_json["Written MB"] = self.write_mb
        results_json["Write time (sec)"] = round(sum(self.write_results),2)
        results_json["Write speed in MB/s"] = round(self.write_mb / sum(self.write_results),2)
        results_json["Read blocks"] = len(self.read_results)
        results_json["Read time (sec)"] = round(sum(self.read_results),2)
        results_json["Read speed in MB/s"] = round(self.write_mb / sum(self.read_results),2)
        with open(output_file,'w') as f:
            json.dump(results_json,f)
            