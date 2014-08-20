#!/usr/bin/env python
'''
Classes to manipulate files.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

from general import x, set_config_property

class scOpen:
    '''
    Class to manipulate files.

    All funcitons execute shell commands (cat, sed) to manipulate files. All
    commands can be printed to screen, and the cut&pasted for manual execution.

    '''
    filename = None

    def __init__(self, filename):
        self.filename = filename

    def esc(self, value):
        return value.replace('\n', '\\\n').replace("/", "\/").replace("&", "&&")

    def add(self, value):
        '''
        Add value to end off file with cat.

        '''
        x("echo '%s' >> %s" % (value, self.filename))

    def add_to_end_of_line(self, search, replace):
        '''
        Add replace string to the end of all lines matching the search string.

        '''
        search = self.esc(search)
        replace = self.esc(replace)
        x("sed -i '/%s/! { /%s/s|$| %s| }' %s" %
            (replace, search, replace, self.filename)
        )

    def remove(self, search):
        '''
        Remove a value from a file using sed.

        '''
        search = self.esc(search)
        x("sed -i '/%s/d' %s" % (search, self.filename))

    def replace(self, search, replace):
        '''
        Replace search string with replace string using sed.

        '''
        search = self.esc(search)
        replace = self.esc(replace)
        x("sed -i 's/%s/%s/g' %s" % (search, replace, self.filename))

    def replace_ex(self, search1, search2, replace):
        '''
        Replace 'search2' with 'replace' on lines containg 'search1'.

        '''
        search1 = self.esc(search1)
        search2 = self.esc(search2)
        replace = self.esc(replace)
        x("sed -i '%s/s|%s|%s|' %s" % (search1, search2, replace, self.filename))

    def replace_add(self, search, replace):
        set_config_property(self.filename, search, replace)

    def remove_eof(self, lines):
        '''
        Remove the last N lines of the file using head.

        '''
        x("head -n-%s %s > /tmp/syco-remove-eof" % (lines, self.filename))
        x("cp /tmp/syco-remove-eof " + self.filename)
