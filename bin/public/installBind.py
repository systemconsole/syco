#! /usr/bin/env python
'''
Install DNS server.

This server will be installed with a chrooted bind dns server. The script will
copy named.conf and zone files from syco/usr/*/var/dns/* to proper named/bind
folder and replace syco defined tags (See below).

The installed bind server will be a master Authoritative to internet users
for defined zones, and recursive for all syco servers.

SERIAL
Used by master and possible future slave server to track the newest dns records
All changed zone files needs an updated serial number. This is done by the
script, the serial number tag ${SERIAL} will updated with the days datetime.

RNDC KEY
Used to allow a slave server to connect to the master server and retrive new
DNS records. The master and the slave server need to have the same rndc key.
The key is generated the first time the master dns server is installed.

INTERNAL VIEW
The DNS server supports different views so that the same dns name can point
to different ips dependning on if you are connecting to the DNS server from the
local network or the internet.

ACTIVE DATA CENTER
The installation supports changing active data center when generating the files.

1. Configure zone files with the ${ACTIVE_DC} tag

    dns-ab.syco.com.  IN A 8.8.8.8
    dns-ac.syco.com.  IN A 8.8.4.4
    dns.syco.com.    IN CNAME dns-${ACTIVE_DC}.syco.com.

2. Install bind

    $ syco install-bind ab

This will install the server and set the datacenter ab to active. By replacing
the ${ACTIVE_DC} tag in all zone files.

TEMPLATE TAGS
These tags can be used in any template file installed by this syco script.

${ACTIVE_DC}
${SERIAL}

READING

Here are some documentation that has been used to learn about how to install
bind/named. Particularly the offical bind doc from isc.org is realy good.
But they should spend some time formatting their html doc, it looks awful.
http://ftp.isc.org/isc/bind9/cur/9.8/doc/arm/Bv9ARM.html

Also the Red Hat documentation is good, to get a hunch about how they do their
bind installations.
https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/ch-DNS_Servers.html

An open source book/guide about bind.
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

__author__ = "daniel@cybercow.se, matte@elino.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.1.0"
__status__ = "Production"


import os
from time import gmtime, strftime

import app
import version
import iptables
import config
import general
from general import x
from scopen import scOpen


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-bind",        install_bind,      "[active-dc]",  help="Install bind 9 server.")
    commands.add("install-bind-zone",   install_bind_zone, "[active-dc]",  help="Reinstall zone files.")
    commands.add("install-bind-client", install_bind_client,               help="Use the syco dns as recursive nameserver.")
    commands.add("uninstall-bind",      uninstall_bind,                    help="Uninstall bind 9 server.")
    commands.add("audit-bind",          audit_bind,                        help="Audit bind installation.")


def install_bind(args):
    '''
    Install bind - The main function

    '''
    app.print_verbose("Install chrooted bind 9 server.")
    version_obj = version.Version("InstallBind", SCRIPT_VERSION)
    version_obj.check_executed()

    # Get cmd line arguments early in the script, to catch user errors.
    active_dc = _get_role_from_cmd_line(args)

    _install_packages()
    _disable_ip_v6_for_named()
    _generate_rndc_key()
    _prepare_chroot()
    _copy_all_configs(active_dc)
    iptables.add_bind_chain()
    iptables.save()

    # Restarting bind to load new settings.
    x("/etc/init.d/named restart")

    version_obj.mark_executed()


def install_bind_zone(args):
    '''
    Install zone files, and reload without restarting bind.

    '''
    if not os.path.exists("/etc/init.d/named"):
       raise Exception("Bind/named is not installed.")

    # Get cmd line arguments early in the script, to catch user errors.
    active_dc = _get_role_from_cmd_line(args)
    _copy_all_configs(active_dc)

    # Restarting bind to load new settings.
    x("/usr/sbin/rndc reload")


def _get_role_from_cmd_line(args):
    '''
    Getting active data center from command line.

    '''
    if len(args) != 2:
        raise Exception(
            "You can only enter active data center, you entered nothing."
        )

    return args[1].lower()


def _install_packages():
    if not os.path.exists("/etc/init.d/named"):
        x("yum install -y bind-chroot bind-utils")
        x("chkconfig --level 35 named on")


def _disable_ip_v6_for_named():
    '''
    Syco servers don't have ipv6 installed, but bind/named tries to do ipv6
    lookups but will only generate error messages. This disables ipv6
    and by that removes some unnecessary error messages.

    http://crashmag.net/disable-ipv6-lookups-with-bind-on-rhel-or-centos

    '''
    named = scOpen("/etc/sysconfig/named")
    named.remove('OPTIONS="-4"')
    named.add('OPTIONS="-4"')


def _generate_rndc_key():
    '''
    Generate a new rndc.key.

    The rndc.key file defines a default command channel and authentication key
    allowing rndc to communicate with named on the local host with no further
    configuration.

    '''
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


def _copy_all_configs(active_dc):
    '''
    Copy all configuration and zone files into proper named folder.

    '''

    _copy_conf(".conf", "/var/named/chroot/etc/", active_dc)
    _copy_conf(".zones", "/var/named/chroot/etc/", active_dc)
    _copy_conf(".zone", "/var/named/chroot/var/named/", active_dc)
    _set_permissions()


def _copy_conf(file_ext, to_folder, active_dc):
    '''
    Copy a set of config/zone files from all syco plugins into a named folder.

    WRNING: If several syco plugins are installed with their own named.conf and
            zone files. That might fuck up the installation.

    '''
    bind_config_subdir = config.host(config.general.get_nameserver_server()).get_bind_conf_subdir()
    if len(bind_config_subdir) > 0 and not bind_config_subdir.startswith('/'):
        bind_config_subdir = "/" + bind_config_subdir

    app.print_verbose("\nCopy config/zone files from all syco plugin modules into a named folder.")
    for plugin_path in app.get_syco_plugin_paths("/var/dns"):
        for zone_fn in os.listdir(plugin_path + bind_config_subdir):
            if zone_fn.endswith(file_ext):
                app.print_verbose("\nConfigure file {0}".format(zone_fn))
                x("cp {0}/{1} {2}".format(plugin_path + bind_config_subdir, zone_fn, to_folder))
                _replace_tags("{0}{1}".format(to_folder, zone_fn), active_dc)


def _replace_tags(filename, active_dc):
    '''
    Copy a template file to proper named folder, and replace tags.

    side - can only be [external|internal]

    '''
    named_conf = scOpen(filename)
    named_conf.replace("${ACTIVE_DC}", active_dc)
    named_conf.replace("${SERIAL}", _generate_serial())


def _generate_serial():
    """
    Return a zone serial number, which is todays datetime.

    ie. 20121006133721
    """
    return strftime("%Y%m%d%H%M%S", gmtime())


def _set_permissions():
    """
    Set permissions on all named config files.

    """
    x("chown named:named -R /var/named/chroot/")
    x("chmod 770 -R /var/named/chroot/")
    x("restorecon -R /var/named/chroot/")


def install_bind_client(args):
    """
    Setup current server to use syco dns server as recursive name server.

    """
    app.print_verbose("Install bind client.")
    version_obj = version.Version("InstallBindClient", SCRIPT_VERSION)
    version_obj.check_executed()

    # Iptables is already configured with iptables._setup_dns_resolver_rules

    general.wait_for_server_to_start(config.general.get_nameserver_server_ip(), "53")

    # Set what resolver to use (this will be rewritten by networkmanager at
    # reboot)
    resolv = scOpen("/etc/resolv.conf")
    resolv.remove("nameserver.*")
    for ip in config.general.get_nameserver_server_ips():
        resolv.add("nameserver {0} ".format(ip))

    # Change config files for networkmanager.
    x("""
        grep -irl dns ifcfg*|xargs \
        sed -i 's/.*\(dns.*\)[=].*/\\1={0}/ig'""".format(
            config.general.get_nameserver_server_ip()
        ), cwd = "/etc/sysconfig/network-scripts"
    )

    version_obj.mark_executed()


def uninstall_bind(args):
    '''
    Uninstall bind.

    '''
    print "Uninstalling DNS Server"
    x("yum erase bind bind-chroot bind-libs bind-utils caching-nameserver -y")
    x("rm -rf /var/named")


def audit_bind(args):
    '''
    Audit bind installation.

    Check if bind installation is properly done.

    '''
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