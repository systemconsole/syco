#!/usr/bin/env python
'''
Cmdline tools used to work with an ldap server.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import subprocess
import hashlib
from time import gmtime, strftime

import app
from app import print_verbose
import config
from general import x
from installOpenLdap import ldapsadd
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("ldap-edit", ldap_edit, help="Edit ldap database.")

def ldap_edit(args):
    '''
    Startup vi with an ldif dump of database, and inserts it after exiting.

    '''
    print_verbose("Edit LDAP database.")
    remove_file()
    dump_database()
    unchanged = hashfile(file(filename(), 'r'))
    edit_database()
    changed = hashfile(file(filename(), 'r'))

    if (unchanged != changed):
        delete_database()
        restore_database()
    else:
        print_verbose("File was not changed.")
    remove_file()

def filename():
    '''
    Returns the name of the temporary dump file.

    '''
    return os.path.expanduser("~/dump.ldif")

def remove_file():
    '''
    Delete dumpfile if existing.

    '''
    if os.path.exists(filename()):
        x("rm " + filename())

def dump_database():
    '''
    Dump all user/domain info in LDAP database to file.

    ldapsearch -D "cn=Manager,dc=syco,dc=net" -w "password#" -b dc=syco,dc=net -LLL > ~/dump.ldif

    '''
    x("ldapsearch -D '%s' -w '%s' -b %s > %s" % (
        'cn=Manager,' + config.general.get_ldap_dn(),
        app.get_ldap_admin_password(),
        config.general.get_ldap_dn(),
        filename()
    ))

def edit_database():
    '''
    Start up (vi) editor of ldif file.

    '''
    print_verbose("Command: vi " + filename())
    subprocess.call(['vi', filename()])

def delete_database():
    '''
    Delete all user/domain info in LDAP database.

    ldapdelete -D "cn=Manager,dc=fareoffice,dc=com" -w -r "t3chn0RAC#" dc=fareoffice,dc=com

    '''
    if os.path.exists(filename()):
        # Create backup of dump file.
        x("cp %s %s%s" % (filename(), filename(), strftime("%Y-%m-%d-%H-%M-%S", gmtime())))

        x("ldapdelete -D '%s' -w '%s' -r %s" % (
            'cn=Manager,' + config.general.get_ldap_dn(),
            app.get_ldap_admin_password(),
            config.general.get_ldap_dn()
        ))
    else:
        raise Exception("Dump file (%s) doesn't exist" % filename())

def restore_database():
    '''
    Restore all user/domain info in LDAP database from file.

    ldapadd -D "cn=Manager,dc=fareoffice,dc=com" -w "t3chn0RAC#" -f dump.ldif

    '''
    x("ldapadd -D '%s' -w '%s' -f %s" % (
        'cn=Manager,' + config.general.get_ldap_dn(),
        app.get_ldap_admin_password(),
        filename()
    ))

def hashfile(afile, blocksize=65536):
    hasher = hashlib.sha512()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

