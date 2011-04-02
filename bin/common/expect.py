#!/usr/bin/env python
'''
Overides of pexpect.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import subprocess, time

import app, install

install.package("pexpect")

import pexpect
import pxssh

class spawn(pexpect.spawn):
  
  # What verbose level should be used with print_verbose
  verbose_level = 2

  def enable_output(self):
    self.verbose_level = 2

  def disable_output(self):
    self.verbose_level = 10

  def expect_loop(self, searcher, timeout = -1, searchwindowsize = -1):
    '''
    Using print_verbose, to get realtime output. Everything else
    is from pexpect.expect_loop.

    '''
    self.searcher = searcher

    if timeout == -1:
        timeout = self.timeout
    if timeout is not None:
        end_time = time.time() + timeout
    if searchwindowsize == -1:
        searchwindowsize = self.searchwindowsize

    try:
        incoming = self.buffer
        freshlen = len(incoming)
        while True: # Keep reading until exception or return.
            app.print_verbose(incoming[ -freshlen : ], self.verbose_level, new_line=False, enable_caption=False)
            index = searcher.search(incoming, freshlen, searchwindowsize)
            if index >= 0:
                self.buffer = incoming[searcher.end : ]
                self.before = incoming[ : searcher.start]
                self.after = incoming[searcher.start : searcher.end]
                self.match = searcher.match
                self.match_index = index
                return self.match_index
            # No match at this point
            if timeout < 0 and timeout is not None:
                raise pexpect.TIMEOUT ('Timeout exceeded in expect_any().')
            # Still have time left, so read more data
            c = self.read_nonblocking (self.maxread, timeout)
            freshlen = len(c)
            time.sleep (0.0001)
            incoming = incoming + c
            if timeout is not None:
                timeout = end_time - time.time()
    except pexpect.EOF, e:
        self.buffer = ''
        self.before = incoming
        self.after = pexpect.EOF
        index = searcher.eof_index
        if index >= 0:
            self.match = pexpect.EOF
            self.match_index = index
            return self.match_index
        else:
            self.match = None
            self.match_index = None
            raise pexpect.EOF (str(e) + '\n' + str(self))
    except pexpect.TIMEOUT, e:
        self.buffer = incoming
        self.before = incoming
        self.after = pexpect.TIMEOUT
        index = searcher.timeout_index
        if index >= 0:
            self.match = pexpect.TIMEOUT
            self.match_index = index
            return self.match_index
        else:
            self.match = None
            self.match_index = None
            raise pexpect.TIMEOUT (str(e) + '\n' + str(self))
    except:
        self.before = incoming
        self.after = None
        self.match = None
        self.match_index = None
        raise


class sshspawn(pxssh.pxssh):

  # What verbose level should be used with print_verbose
  verbose_level = 2

  def enable_output(self):
    self.verbose_level = 2

  def disable_output(self):
    self.verbose_level = 10

  def expect_loop(self, searcher, timeout = -1, searchwindowsize = -1):
    '''
    Using print_verbose, to get realtime output. Everything else
    is from pexpect.expect_loop.

    '''
    self.searcher = searcher

    if timeout == -1:
        timeout = self.timeout
    if timeout is not None:
        end_time = time.time() + timeout
    if searchwindowsize == -1:
        searchwindowsize = self.searchwindowsize

    try:
        incoming = self.buffer
        freshlen = len(incoming)
        while True: # Keep reading until exception or return.
            app.print_verbose(incoming[ -freshlen : ], self.verbose_level, new_line=False, enable_caption=False)
            index = searcher.search(incoming, freshlen, searchwindowsize)
            if index >= 0:
                self.buffer = incoming[searcher.end : ]
                self.before = incoming[ : searcher.start]
                self.after = incoming[searcher.start : searcher.end]
                self.match = searcher.match
                self.match_index = index
                return self.match_index
            # No match at this point
            if timeout < 0 and timeout is not None:
                raise pexpect.TIMEOUT ('Timeout exceeded in expect_any().')
            # Still have time left, so read more data
            c = self.read_nonblocking (self.maxread, timeout)
            freshlen = len(c)
            time.sleep (0.0001)
            incoming = incoming + c
            if timeout is not None:
                timeout = end_time - time.time()
    except pexpect.EOF, e:
        self.buffer = ''
        self.before = incoming
        self.after = pexpect.EOF
        index = searcher.eof_index
        if index >= 0:
            self.match = pexpect.EOF
            self.match_index = index
            return self.match_index
        else:
            self.match = None
            self.match_index = None
            raise pexpect.EOF (str(e) + '\n' + str(self))
    except pexpect.TIMEOUT, e:
        self.buffer = incoming
        self.before = incoming
        self.after = pexpect.TIMEOUT
        index = searcher.timeout_index
        if index >= 0:
            self.match = pexpect.TIMEOUT
            self.match_index = index
            return self.match_index
        else:
            self.match = None
            self.match_index = None
            raise pexpect.TIMEOUT (str(e) + '\n' + str(self))
    except:
        self.before = incoming
        self.after = None
        self.match = None
        self.match_index = None
        raise

  def synch_original_prompt (self):

      """This attempts to find the prompt. Basically, press enter and record
      the response; press enter again and record the response; if the two
      responses are similar then assume we are at the original prompt. """

      # All of these timing pace values are magic.
      # I came up with these based on what seemed reliable for
      # connecting to a heavily loaded machine I have.
      # If latency is worse than these values then this will fail.      
      self.sendline()
      time.sleep(0.5)
      self.read_nonblocking(size=10000,timeout=1) # GAS: Clear out the cache before getting the prompt
      time.sleep(0.1)
      self.sendline()
      time.sleep(0.5)
      x = self.read_nonblocking(size=1000,timeout=1)
      time.sleep(0.1)
      self.sendline()
      time.sleep(0.5)
      a = self.read_nonblocking(size=1000,timeout=1)
      time.sleep(0.1)
      self.sendline()
      time.sleep(0.5)
      b = self.read_nonblocking(size=1000,timeout=1)
      ld = self.levenshtein_distance(a,b)
      len_a = len(a)
      if len_a == 0:
          return False
      if float(ld)/len_a < 0.4:
          return True
      return False

