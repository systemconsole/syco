#!/usr/bin/env python
'''
Application global wide helper functions.

TODO:
Should be
import password
print password.svn
print password.mysql
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
import re
import socket
import sys
import time
import subprocess

from constant import *
import passwordstore

def _get_password_store():
    '''
    Get a password store object.

    '''
    if (not _get_password_store.password_store):
        _get_password_store.password_store = passwordstore.PasswordStore(PASSWORD_STORE_PATH)

    return _get_password_store.password_store

_get_password_store.password_store = None

def _get_password(service, user_name):
    '''
    Get a password from the password store.g

    '''
    password = _get_password_store().get_password(service, user_name)
    _get_password_store().save_password_file()
    return password

def get_custom_password(service, user_name):

    if service is None or user_name is None:
        raise Exception("None service and user name not allowed, please specify both")

    return _get_password(service, user_name)

def get_master_password():
    '''
    Get a password from the password store.

    '''
    password = _get_password_store().get_master_password()
    _get_password_store().save_password_file()
    return password

def get_root_password():
    '''The linux shell root password.'''
    return _get_password("linux", "root")

def get_root_password_hash():
    '''
    Openssl hash of the linux root password.

    '''
    root_password = get_root_password()
    p = subprocess.Popen("openssl passwd -1 '" + root_password + "'", stdout=subprocess.PIPE, shell=True)
    hash_root_password, stderr = p.communicate()
    return str(hash_root_password.strip())

def get_user_password(username):
    '''The linux shell password for a specific user.'''
    return _get_password("linux", username)

def get_ca_password():
    '''The password used when creating CA certificates'''
    return get_root_password()

def get_svn_password():
    '''The svn password for user syscon_svn'''
    return _get_password("svn", "syscon")

def get_ldap_admin_password():
    '''The ldap admin password.'''
    return _get_password("ldap", "admin")

def get_ldap_sssd_password():
    '''The password that is used by sssd to connect to the ldap-server.'''
    return _get_password("ldap", "sssd")

def get_glassfish_master_password():
    '''Used to sign keystore, never transfered over network.'''
    return _get_password("glassfish", "master")

def get_glassfish_admin_password():
    '''Login to asadmin or web admin console'''
    return _get_password("glassfish", "admin")

def get_switch_icmp_password():
    '''The password for read-only SNMP switch access.'''
    return _get_password("switch", "snmp")

def get_mysql_root_password():
    '''The root password for the mysql service.'''
    return _get_password("mysql", "root")

def get_mysql_monitor_password():
    '''
    The monitor password for the mysql service.

    Used by icinga nrpe plugins.

    '''
    return _get_password("mysql", "monitor")

def get_mysql_backup_password():
    '''
    The backup password for the mysql service.

    Used by backup scripts.

    '''
    return _get_password("mysql", "backup")

'''A user password for the mysql service.'''


def get_mysql_password(env):
    return _get_password("mysql", env)

def get_mysql_integration_password():
    '''A user password for the mysql service.'''
    return _get_password("mysql", "integration")

def get_mysql_stable_password():
    '''A user password for the mysql service.'''
    return _get_password("mysql", "stable")

def get_mysql_uat_password():
    '''A user password for the mysql service.'''
    return _get_password("mysql", "uat")

def get_mysql_production_password():
    '''A user password for the mysql service.'''
    return _get_password("mysql", "production")

def get_redis_production_password():
  '''A user password for the redis service.'''
  return _get_password("redis", "production")

def get_haproxy_sps_ping_password():
  '''A user password for the haproxy ping.'''
  return _get_password("haproxy-sps-ping", "haproxy")

def init_mysql_passwords():
    get_mysql_root_password()
    get_mysql_monitor_password()
    get_mysql_backup_password()
    get_mysql_integration_password()
    get_mysql_stable_password()
    get_mysql_uat_password()
    get_mysql_production_password()

def init_all_passwords():
    '''
    Ask the user for all passwords used by syco, and add to passwordstore.

    '''
    get_root_password()
    get_svn_password()
    get_ldap_admin_password()
    get_ldap_sssd_password()
    get_glassfish_master_password()
    get_glassfish_admin_password()
    get_user_password("glassfish")
    get_switch_icmp_password()
    get_redis_production_password()
    get_haproxy_sps_ping_password()
    init_mysql_passwords()
