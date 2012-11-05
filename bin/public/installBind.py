#! /usr/bin/env python
'''
Install DNS server.

This server will be installed with a chrooted bind dns server. The script will
read DNS config files from syco/var/dns and generate dns enteries for the
server in config files.

$syco install-dns master
Will install the master bind server. The server will be setup so that the slave
server are allowd to connect to the master server and transfer DNS records from
it.

$syco install-dns slave
Will install the slave bind server. The slave DNS server will connect to the
master bind server and retrive changes to the DNS records.

SERIAL
Used by both master and slave server to track the newest dns records. All
changes to the DNS have to be updated with a serial number. When the script is
executed, the serial number will update itself and the templates used to
generate the config files. To reset the serial number set the serial number to
0 in the master-template.zone and the slave-template.zone

RNDC KEY
Used to allow the slave server to connect to the master server and retrive new
DNS records. The master and the slave server need to have the same rndc key.
The key is generated the first time the master dns server is installed. The
slave server uses ssh to retrive the key from the master server.

Configuration
-------------

In the file zone.cfg the main config options is inserted

[config]
range:10.100.100.0/24  ; Range of server network
localnet:192.168/16    ; Range of the client network allowed to do recursive reqest
forward1:8.8.8.8       ; DNS forwarder 1
forward2:4.4.4.4       ; DNS forwarder 2
ipmaster:10.100.100.10 ; IP of master DNS
ipslave:10.100.100.241 ; IP of slave DNS

# The active data center
# in you cnames set $DATA_CENTER$ and it will be changed
data_center:av

# Zone to be used
# Create a file called exempel.org in the folder that contains dns records.
[zone]
syco.net:100.100.10
syco.com:192.168.0.0

ZONE Config
-----------

To edit zones to the dns name create one file with the same name as the dns name.
For exempel syco.net create the file called syco.net. Create two blocks in that
file.

[syco.net_arecords]
www:178.78.197.210

[syco.net_cname]
web:www

The first one is for A records and the second one is for cnames.
The script will generate dns files from the enteries.

Private ZONE
in folder var/dns/ are exempel configs.
Put your correct zone.cfg and zone files in your syco-privart/var/dns.
Syco will always look in your syco-private/var/dns folder for file zone.cfg and
zone files syco.com.

INTERNAL VIEW
-------------

The DNS server support different views so that the same dns name can be pointed
to different ips dependning on if you are connecting to the DNS server from you
local network or the internet. As default all entries will be the same if you not
specify in the zone file the differt name.

To add internal ip to be used add in you configfile for you dns name

[internal_syco.net_arecords]
www:10.100.0.4

[internal_syco.net_cname]
mail:mail-tp

The script will then generate this config to be used for internal view and the
other will be used for external view.

PRIMARY DATA CENTER
-------------------

The DNS server support changing primary data center when generating the files.
By in the configfile setting

1. The data center named av will be used.
data_center:av

2. Setup an a record to both locations
av-server.syco.net:10.100.0.1
tc-server.syco.net:99.100.100.1

3. Setup a cname to the a record
server:server-av

4. Setup for auto changing data center
change the cname record above to
server:$DATA_CENTER$-server

Template tags
============

These tags can be used in any template file installed by this syco script.

Defined in zone.cfg
-------------------

${IPMASTER}
${IPSLAVE}
${RANGE}
${FORWARD1}
${FORWARD2}
${DATA_CENTER}

Defined programatically by install script
-----------------------------------------

${ZONE_FILENAME}
${NAMEZONE}
${SIDE}
${SERIAL}

READING
=======

http://ftp.isc.org/isc/bind9/cur/9.8/doc/arm/Bv9ARM.html
https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/ch-DNS_Servers.html
http://www.zytrax.com/books/dns/

http://www.philchen.com/2007/04/04/configuring-reverse-dns
http://www.linuxtopia.org/online_books/rhel6/rhel_6_deployment/rhel_6_deployment_ch-The_BIND_DNS_Server.html
http://www.wains.be/index.php/2007/12/13/centos-5-chroot-dns-with-bind/
http://www.broexperts.com/2012/03/linux-dns-bind-configuration-on-centos-6-2/
http://www.andrewzammit.com/blog/setting-up-bind-9-on-centos-6-and-securing-a-private-nameserver-on-the-internet/


Test Tools
==========

* http://www.dnswalk.nu/index.php
* http://freecode.com/projects/Dlint
* http://www.zonecheck.nu/

TODO
----
* https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/s1-BIND.html


'''

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import ConfigParser
import os
import re
import sys
from time import gmtime, strftime

import app
import config
import general
import version
from general import x
from scopen import scOpen
from ssh import scp_from


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-bind",   install_bind,   "[master|slave]",  help="Install bind 9 server.")
    commands.add("uninstall-bind", uninstall_bind,  help="Uninstall bind 9 server.")
    commands.add("audit-bind", audit_bind,  help="Check if audit installation is correct.")


class BindConfig():
    dnsrange = None
    localnet = None
    forward1 = None
    forward2 = None
    ipmaster = None
    ipslave = None
    data_center = None
    zones = None

    def __init__(self):
        zone = ConfigParser.SafeConfigParser()
        zone.read(app.SYCO_PATH + 'usr/syco-private/var/dns/zone.cfg')
        self.dnsrange = zone.get('config', 'range')
        self.localnet = zone.get('config', 'localnet')
        self.forward1 = zone.get('config', 'forward1')
        self.forward2 = zone.get('config', 'forward2')
        self.ipmaster = zone.get('config', 'ipmaster')
        self.ipslave = zone.get('config', 'ipslave')
        self.data_center = zone.get('config', 'data_center')


def _get_bind_config():
    if _get_bind_config.bind_config == None:
        _get_bind_config.bind_config = BindConfig()
    return _get_bind_config.bind_config
_get_bind_config.bind_config = None


def install_bind(args):
    app.print_verbose("Install chrooted bind 9 server.")
    version_obj = version.Version("InstallBind", SCRIPT_VERSION)
    version_obj.check_executed()

    # Get cmd line arguments early in the script, to catch user errors.
    role = _get_role_from_cmd_line(args)

    _install_packages()
    _disable_ip_v6_for_named()
    _generate_rndc_key()
    _prepare_chroot()

    # Setup named.conf with proper settings
    _copy_conf_file(
        "{0}var/dns/{1}-named.conf".format(app.SYCO_PATH, role),
        "/var/named/chroot/etc/named.conf"
    )

    _copy_plugin_zone_files(role, 'internal')
    _copy_plugin_zone_files(role, 'external')

    _set_permissions()

    # Restarting bind to load new settings.
    x("/etc/init.d/named restart")

    version_obj.mark_executed()


def _get_role_from_cmd_line(args):
    '''
    Getting arguments from command line.

    master = setting up master server
    slave = setting up slave server

    '''

    if len(args) != 2:
        raise Exception(
            "You can only enter master or slave, you entered nothing."
        )

    role = args[1]
    if (role != "master"):
        raise Exception(
            "Only master server can be installed, you entered %s." % role
        )

    return role.lower()


def _install_packages():
    if not os.path.exists("/etc/init.d/named"):
        x("yum install -y bind-chroot bind-utils")
        x("chkconfig --level 35 named on")


def _disable_ip_v6_for_named():
    '''
    Syco servers don't have ipv6 installed, but bind/named tries to do ipv6
    lookups but will only genereate error messages. This disables ipv6
    and by that removes some unnecessary error messages.

    http://crashmag.net/disable-ipv6-lookups-with-bind-on-rhel-or-centos

    '''
    named = scOpen("/etc/sysconfig/named")
    named.remove('OPTIONS="-4"')
    named.add('OPTIONS="-4"')


def _generate_rndc_key():
    if not os.path.exists("/etc/rndc.key"):
        app.print_verbose("Generate /etc/rndc.key, takes some time.")
        x("rndc-confgen -a -c /etc/rndc.key")
        x("chown named /etc/rndc.key")
        x("chmod 600 /etc/rndc.key")


def _prepare_chroot():
    '''
    Prepare the chroot folder structure with required default files.

    '''
    app.print_verbose(
        "Prepare the chroot folder structure with required default files."
    )

    x("mkdir -p /var/named/chroot/var/named/data")
    x("mkdir -p /var/named/chroot/var/named/dynamic")

    x("cp -f /var/named/named.ca /var/named/chroot/var/named/named.ca")
    x("cp -f /var/named/named.empty /var/named/chroot/var/named/named.empty")
    x("cp -f /var/named/named.localhost /var/named/chroot/var/named/named.localhost")
    x("cp -f /var/named/named.loopback /var/named/chroot/var/named/named.loopback")






def _copy_conf_file(from_fn, to_fn, zone_fn = None, zone = None, side = None, rzone = False):
    '''
    Copy a template file to proper named folder, and replace tags.

    side - can only be [external|internal]

    '''
    bn = _get_bind_config()

    app.print_verbose("Configure file {0}".format(to_fn))
    x("cp -f %s %s" % (from_fn, to_fn))

    named_conf = scOpen(to_fn)
    named_conf.replace("${IPMASTER}", bn.ipmaster)
    named_conf.replace("${IPSLAVE}",  bn.ipslave)
    named_conf.replace("${RANGE}",    bn.dnsrange)
    named_conf.replace("${LOCALNET}", bn.localnet)
    named_conf.replace("${FORWARD1}", bn.forward1)
    named_conf.replace("${FORWARD2}", bn.forward2)
    named_conf.replace("${DATA_CENTER}", bn.data_center)

    if not zone_fn:
        zone_fn = ""
    named_conf.replace("${ZONE_FILENAME}", zone_fn)

    if not zone:
        zone = ""
    named_conf.replace("${NAMEZONE}", zone)

    if rzone:
        rzone = ".in-addr.arpa"
    else:
        rzone = ""
    named_conf.replace("${RZONE}", rzone)

    if not side:
        side = ""
    named_conf.replace("${SIDE}", side)

    named_conf.replace("${SERIAL}", _generate_serial())


def _generate_serial():
    return strftime("%Y%m%d%H%M%S", gmtime())


def _copy_plugin_zone_files(role, side):
    '''
    Copy zone files from all syco plugin modules into proper named folder.

    '''
    _clear_side_zone(side)
    app.print_verbose("Copy zone files from all syco plugin modules into named chroot.")
    for plugin_path in get_syco_plugin_paths():
        for zone_fn in os.listdir(plugin_path):
            _copy_global_zone(plugin_path, zone_fn)
            _copy_side_zone(plugin_path, zone_fn, role, side)


def get_syco_plugin_paths():
    '''
    Generator of fullpath to all syco plugins /var/dns folder.

    '''
    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + "/var/dns/")
            if (os.access(plugin_path, os.F_OK)):
                yield plugin_path


def _copy_global_zone(plugin_path, zone_fn):
    '''
    Copy global.zone file if existing into proper named folder.

    This file is probably then used by internal.zone and/or
    external.zone file.

    '''
    if zone_fn.endswith('.global.zone'):
        _copy_conf_file(
            '{0}/{1}'.format(plugin_path, zone_fn),
            '/var/named/chroot/var/named/{0}'.format(zone_fn)
        )


def _side_zone_fn(side):
    return "/var/named/chroot/etc/named.syco.{0}.zones".format(side)


def _clear_side_zone(side):

    x("rm {0}".format(_side_zone_fn(side)))
    x("touch {0}".format(_side_zone_fn(side)))


def _copy_side_zone(plugin_path, zone_fn, role, side):
    '''
    Copy internal/external zone files if existing into proper named folder.

    '''
    zone_ext = '.{0}.zone'.format(side)
    rzone_ext = '.{0}.rzone'.format(side)
    if zone_fn.endswith(zone_ext):
        zone = zone_fn[:-len(zone_ext)]
        _copy_zone(plugin_path, zone_fn, role, side, zone)
    elif zone_fn.endswith(rzone_ext):
        zone = zone_fn[:-len(rzone_ext)]
        _copy_zone(plugin_path, zone_fn, role, side, zone, True)


def _copy_zone(plugin_path, zone_fn, role, side, zone, rzone = False):
    # Copy the zone file form the syco plugin folder to named.
    _copy_conf_file(
        '{0}/{1}'.format(plugin_path, zone_fn),
        '/var/named/chroot/var/named/{0}'.format(zone_fn)
    )

    # If currently handling an internal zone, adding all syco servers to
    # the internal zone.
    _add_syco_servers(
        zone, '/var/named/chroot/var/named/{0}'.format(zone_fn)
    )

    # Add zone to be included by named.conf
    tmp_fn = "{0}named.syco.zones".format(general.get_install_dir())
    _copy_conf_file(
        "{0}var/dns/{1}-zone.conf".format(app.SYCO_PATH, role),
        tmp_fn,
        zone_fn,
        zone,
        side,
        rzone
    )

    x("cat {0} >> {1}".format(tmp_fn, _side_zone_fn(side)))


def _add_syco_servers(zone, filename):
    # Disabled this, currently we think it's better to set all ips/domains
    # in the zone files.
    return
    if zone == config.general.get_resolv_domain():
        f = scOpen(filename)
        for hostname in config.get_servers():
            f.add("{0}.{1}. IN A {2}".format(
                hostname, zone, config.host(hostname).get_front_ip())
            )


def _set_permissions():
    '''
    Set permissions on all named config files.

    '''
    x("chown named:named -R /var/named/chroot/")
    x("chmod 770 -R /var/named/chroot/")
    x("restorecon -R /var/named/chroot/")


def uninstall_bind(args):
  print "Uninstalling DNS Server"
  x("yum erase bind bind-chroot bind-libs bind-utils caching-nameserver -y")
  x("rm -rf /var/named")


def audit_bind(args):
    error = False
    # The named-checkconf program checks the syntax of a named.conf file.
    result = x("named-checkconf -t /var/named/chroot /etc/named.conf")
    if result:
        app.print_verbose("ERROR: Invalid data in config file\n{0}".format(result))
        error = True

    #
    search = 'server is up and running'
    result = x('/etc/init.d/named status |grep "{0}"'.format(search))
    if result.strip() != search:
        app.print_verbose("ERROR: Server is down")
        error = True

    if error:
        app.print_verbose("Fail - named didn't pass audit.")
    else:
        app.print_verbose("Ok - named did pass audit.")
