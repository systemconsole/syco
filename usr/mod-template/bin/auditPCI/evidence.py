#!/usr/bin/env python
'''
Helper function to gather evidence.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import datetime
import socket

from utils import x


class Evidence:
    caption = None
    now = None
    _output = None
    _exclude = None

    def __init__(self, requirment, description):
        hostname = socket.gethostname()
        self.caption = '{0}_{1}_{2}'.format(requirment, hostname, description)
        self.now = datetime.datetime.now().strftime('%y%m%d')
        self.clear()

    def clear(self):
        self._output = ''
        self._exclude = []

    def exclude(self, regexp):
        self._exclude.append(regexp)

    def gather(self, cmd):
        self._output += '--- Start '
        self._output += '-' * (80 - 10)
        self._output += '\n'
        self._output += '{0}\n'.format(cmd)
        self._output += x(cmd)
        self._output += '--- End '
        self._output += '-' * (80 - 7)
        self._output += '\n'

    def store(self):
        # /var/lib/syco/dynamic/2.2.3_bounce-av_netstat_130121.txt
        folder = '/tmp/syco/dynamic'
        self._store_file(
            folder,
            "{0}/{1}_{2}".format(folder, self.caption, self.now)
        )

        #/var/lib/syco/static/2.2.3_bounce-av_netstat.txt
        folder = '/tmp/syco/static'
        self._store_file(
            folder,
            "{0}/{1}".format(folder, self.caption)
        )

    def _store_file(self, folder, filename):
        print('Create {0}'.format(filename))
        x('mkdir -p {0}'.format(folder))
        with open(filename, 'w') as f:
            f.write(self._output)

