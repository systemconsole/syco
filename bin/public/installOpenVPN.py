#!/usr/bin/env python
'''
Install the server to act as a openvpn server

Will use x.x.x.0:1194 as the vpn client net taken from log.network in cfg file.

More info about openvpn.
http://openvpn.net/index.php/open-source/documentation/howto.html
http://notes.brooks.nu/2008/08/openvpn-setup-on-centos-52/
http://www.howtoforge.com/openvpn-server-on-centos-5.2
http://www.throx.net/2008/04/13/openvpn-and-centos-5-installation-and-configuration-guide/

TODO: yum installopenvpn-auth-ldap ??

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
import stat

from general import x, download_file, md5checksum, get_install_dir
from scopen import scOpen
import app
import config
import general
import install
import iptables
import net
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.

# EASY RSA DOWNLOAD URL
EASY_RSA_DOWNLOAD = "https://github.com/OpenVPN/easy-rsa/archive/v2.2.0.zip"
EASY_RSA_MD5 = 'd2e760402541e4b534b4bab5f92455aa'

SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-openvpn-server", install_openvpn_server, help="Install openvpn-server on the current server.")
    commands.add("install-openvpn-client-certs", build_client_certs, help="Build client certs on the openvpn server.")

def copy_easy_rsa():

    # Downloading and md5 checking
    download_file(EASY_RSA_DOWNLOAD, "v2.2.0.zip",md5=EASY_RSA_MD5)

    # Unzipping and moving easy-rsa files
    install_dir = get_install_dir()
    x("yum -y install unzip")
    x("unzip {0}{1} -d {0}".format(install_dir,"v2.2.0.zip"))
    x("mv {0}easy-rsa-2.2.0/easy-rsa/2.0 /etc/openvpn/easy-rsa".format(install_dir))
    x("yum -y remove unzip")

def install_openvpn_server(args):
    '''
    The actual installation of openvpn server.

    '''
    app.print_verbose("Install openvpn server version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallOpenvpnServer", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords
    enable_ldap = config.general.get_option("openvpn.ldap.enable", "false")
    x("yum -y install openvpn")

    if enable_ldap:
        app.get_ldap_sssd_password()
        x("yum -y install openvpn-auth-ldap")

    if not os.access("/etc/openvpn/easy-rsa", os.F_OK):

        copy_easy_rsa()

        # Install server.conf
        server_conf = "/etc/openvpn/server.conf"
        x("cp " + app.SYCO_PATH + "/var/openvpn/server.conf %s" % server_conf)
        scOpen(server_conf).replace('${EXTERN_IP}',  net.get_public_ip())
        scOpen(server_conf).replace('${OPENVPN_NETWORK}',  config.general.get_openvpn_network())
        scOpen(server_conf).replace('${PUSH_ROUTES}',  _get_push_routes())

        ccd_enabled = config.general.get_option("openvpn.ccd.enable", "false").lower()
        ccd_dir = ""
        client_routes = ""
        c2c = ""

        if ccd_enabled:
            ccd_dir = "client-config-dir ccd"
            client_routes = _get_client_routes()
            c2c = "client-to-client"

        scOpen(server_conf).replace('${CCD_DIR}', ccd_dir)
        scOpen(server_conf).replace('${CLIENT_ROUTES}', client_routes)
        scOpen(server_conf).replace('${CLIENT_TO_CLIENT}', c2c)
        scOpen(server_conf).replace('${DHCP_DNS_SERVERS}', _get_dhcp_dns_servers())

        # Prepare the ca cert generation.
        fn = "/etc/openvpn/easy-rsa/vars"
        scOpen(fn).replace('[\s]*export KEY_COUNTRY.*',  'export KEY_COUNTRY="' + config.general.get_country_name() + '"')
        scOpen(fn).replace('[\s]*export KEY_PROVINCE.*', 'export KEY_PROVINCE="' + config.general.get_state() + '"')
        scOpen(fn).replace('[\s]*export KEY_CITY.*',     'export KEY_CITY="' + config.general.get_locality() + '"')
        scOpen(fn).replace('[\s]*export KEY_ORG.*',      'export KEY_ORG="' + config.general.get_organization_name() + '"')
        scOpen(fn).replace('[\s]*export KEY_OU.*',       'export KEY_OU="' + config.general.get_organizational_unit_name() + '"')
        scOpen(fn).replace('[\s]*export KEY_EMAIL.*',    'export KEY_EMAIL="' + config.general.get_admin_email() + '"')

        # Can't find the current version of openssl.cnf.
        scOpen("/etc/openvpn/easy-rsa/whichopensslcnf").replace("\[\[\:alnum\:\]\]", "[[:alnum:]]*")

        # Generate CA cert
        os.chdir("/etc/openvpn/easy-rsa/")
        x(". ./vars;./clean-all;./build-ca --batch;./build-key-server --batch server;./build-dh")
        x("cp /etc/openvpn/easy-rsa/keys/{ca.crt,ca.key,server.crt,server.key,dh1024.pem} /etc/openvpn/")

        #Generation TLS key
        os.chdir("/etc/openvpn/")
        x("openvpn --genkey --secret ta.key")

        # To prevent error "TXT_DB error number 2" when running ./build-key-pkcs12 --batch xxx"
        scOpen("/etc/openvpn/easy-rsa/keys/index.txt.attr").replace("unique_subject.*", "unique_subject = no")

    # To be able to route trafic to internal network
    net.enable_ip_forward()

    if enable_ldap:
        _setup_ldap()

    iptables.add_openvpn_chain()
    iptables.save()

    x("/etc/init.d/openvpn restart")
    x("/sbin/chkconfig openvpn on")

    build_client_certs(args)

    version_obj.mark_executed()


def _get_client_routes():
    '''
    Determine client routes from config
    '''

    client_routes = config.general.get_option("openvpn.ccd.routes", "")
    client_routes_res = ""
    if client_routes is not None and client_routes != "":
        routes = _parse_routes(client_routes)

        for route_network in routes.keys():
            client_routes_res += "route " + route_network + " " + routes[route_network] + "\n"

    return client_routes_res


def _get_dhcp_dns_servers():
    dns_servers = config.general.get_option("openvpn.dhcp.dns", "")
    dns_servers_res =""
    if dns_servers is not None and dns_servers != "":

        for dns_server in dns_servers.split():
            dns_servers_res += "push \"dhcp-option DNS " + dns_server + "\"\n"

    return dns_servers_res


def _get_push_routes():
    '''
    Determine push routes from config or default to frontnet and backnet.
    '''

    push_routes = config.general.get_option("openvpn.push_routes", "")

    if push_routes is None or push_routes == "":
        #Fall Back to front-net and back net if enabled
        push_routes = "push \"route " + config.general.get_front_network() + " " + config.general.get_front_netmask()\
            + "\"\n"

        if config.general.is_back_enabled():
            push_routes += "push \"route " + config.general.get_back_network() + " " + config.general.get_back_netmask()\
                + "\n"

    else:
        routes = _parse_routes(push_routes)

        for route_network in routes.keys():
            push_routes += "push \"route " + route_network + " " + routes[route_network] + "\"\n"

    return push_routes


def _parse_routes(route_str):
    '''
    Parse a route string to a dict of routes
    Different routes are separated by comma and network/mask are seperated by colon
    e.g. 10.10.10.0:255.255.255.0,10.10.11.0:255.255.255.248
    '''
    routes_dict = {}
    route_list = route_str.split(",")

    for route in route_list:
        route_pair = route.split(":")
        if len(route_pair) != 2:
            raise Exception("Expected push routes of format: <network>:<netmask> and several "
                            "routes separated by comma")
        routes_dict[route_pair[0]] = route_pair[1]

    return routes_dict


def _setup_ldap():
    '''
    Configure openvpn to authenticate through LDAP.

    '''
    ldapconf = scOpen("/etc/openvpn/auth/ldap.conf")
    ldapconf.replace("^\\s*URL\s*.*","\\tURL\\tldaps://%s" % config.general.get_ldap_hostname())
    ldapconf.replace("^\s*# Password\s*.*","\\tPassword\\t%s" % app.get_ldap_sssd_password())
    ldapconf.replace("^\s*# BindDN\s*.*","\\tBindDN\\tcn=sssd,%s" % config.general.get_ldap_dn())
    ldapconf.replace("^\s*TLSEnable\s*.*","\\t# TLSEnable\\t YES")

    # Deal with certs
    ldapconf.replace("^\s*TLSCACertFile\s*.*","\\tTLSCACertFile\\t /etc/openldap/cacerts/ca.crt")
    ldapconf.replace("^\s*TLSCACertDir\s*.*","\\tTLSCACertDir\\t /etc/openldap/cacerts/")
    ldapconf.replace("^\s*TLSCertFile\s*.*","\\tTLSCertFile\\t /etc/openldap/cacerts/client.crt")
    ldapconf.replace("^\s*TLSKeyFile\s*.*","\\tTLSKeyFile\\t /etc/openldap/cacerts/client.key")

    # Auth
    ldapconf.replace("^\s*BaseDN\s*.*","\\BaseDN\\t \"%s\"" % config.general.get_ldap_dn() )
    ldapconf.replace("^\s*SearchFilter\s*.*","\\tSearchFilter\\t \"(\\&(uid=%u)(employeeType=Sysop))\"")

    x('echo "plugin /usr/lib64/openvpn/plugin/lib/openvpn-auth-ldap.so /etc/openvpn/auth/ldap.conf" >> /etc/openvpn/server.conf ')


def build_client_certs(args):
    install.package("zip")
    os.chdir("/etc/openvpn/easy-rsa/keys")
    general.set_config_property("/etc/cronjob", "01 * * * * root run-parts syco build_client_certs", "01 * * * * root run-parts syco build_client_certs")

    # Create client.conf
    clientConf = "/etc/openvpn/easy-rsa/keys/client.conf"
    x("cp " + app.SYCO_PATH + "/var/openvpn/client.conf %s" % clientConf)
    scOpen(clientConf).replace('${OPENVPN.HOSTNAME}',  config.general.get_openvpn_hostname())

    x("cp " + app.SYCO_PATH + "/doc/openvpn/install.txt .")

    for user in os.listdir("/home"):
        cert_already_installed=os.access("/home/" + user +"/openvpn_client_keys.zip", os.F_OK)
        valid_file="lost+found" not in user
        if valid_file and not cert_already_installed:
            os.chdir("/etc/openvpn/easy-rsa/")
            general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_CN.*',    'export KEY_CN="' + user + '"')
            general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_NAME.*',  'export KEY_NAME="' + user + '"')

            general.set_config_property("/etc/openvpn/easy-rsa/build-key-pkcs12", '.*export EASY_RSA.*', 'source ./vars;export EASY_RSA="${EASY_RSA:-.}"')

            out = general.shell_exec("./build-key-pkcs12 --batch " + user,
                                     cwd="/etc/openvpn/easy-rsa/",
                                     events={'(?i)Enter Export Password:':'\n', '(?i)Verifying - Enter Export Password:':'\n'}
            )
            app.print_verbose(out)

            # Config client.crt
            general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^cert.*crt", "cert " + user + ".crt")
            general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^key.*key", "key " + user + ".key")

            os.chdir("/etc/openvpn/easy-rsa/keys")
            x("zip /home/" + user +"/openvpn_client_keys.zip ca.crt " + user + ".crt " + user + ".key " + user + ".p12 client.conf install.txt /etc/openvpn/ta.key")
            # Set permission for the user who now owns the file.
            os.chmod("/home/" + user +"/openvpn_client_keys.zip", stat.S_IRUSR | stat.S_IRGRP)
            general.shell_exec("chown " + user + ":users /home/" + user +"/openvpn_client_keys.zip ")
