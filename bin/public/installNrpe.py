#!/usr/bin/env python
'''
Install nrpe


'''

import os

from general import generate_password, get_install_dir, x
import app
import config
import constant
import general
import install
import iptables
import net
import scopen
import version


__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Elis Kullberg"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Development"


HP_HEALTH_FILENAME="hp-health-8.7.0.22-17.rhel6.x86_64.rpm"
HP_HEALTH_URL="http://downloads.linux.hp.com/SDR/psp/RedHatEnterpriseES/6.0/packages/x86_64/{0}".format(HP_HEALTH_FILENAME)
HP_HEALTH_MD5="b3c2b453621d5097c1fdefdb3f25199d"


SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-nrpe-client", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")


def install_nrpe(args):
    '''
    Install a hardened NRPE server (to be run on every host), plugins and commands.

    '''
    app.print_verbose("Installing nrpe")
    version_obj = version.Version("installNrpe", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nrpe(args)
    version_obj.mark_executed()


def _install_nrpe(args):
    '''
    The nrpe installation is quite standard - except that the stock NRPE.conf is replaced with a prepped one.
    Server only listens to this IP. Not super safe but better than nothing. Also, argument parsing is _disabled_.

    '''
    install.epel_repo()

    # Confusing that nagios-plugins-all does not really include all plugins
    x("yum install nagios-plugins-all nrpe nagios-plugins-nrpe php-ldap nagios-plugins-perl perl-Net-DNS perl-Proc-ProcessTable perl-Date-Calc -y")


    # Move object structure and prepare conf-file
    x("rm -rf /etc/nagios/nrpe.d")
    x("rm -rf /etc/nagios/nrpe.cfg")
    x("cp -r {0}syco-private/var/nagios/nrpe.d /etc/nagios/".format(constant.SYCO_USR_PATH))
    x("cp {0}syco-private/var/nagios/nrpe.cfg /etc/nagios/".format(constant.SYCO_USR_PATH))

    # Set permissions for read/execute under NRPE-user
    x("chown -R root:nrpe /etc/nagios/")

    # Extra plugins installed
    _install_nrpe_plugins()

    # Allow only monitor to query NRPE
    monitor_server_front_ip = config.host(config.general.get_monitor_server()).get_front_ip()
    app.print_verbose("Setting monitor server:" + monitor_server_front_ip)
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.cfg")
    nrpe_config.replace("$(MONITORIP)" ,monitor_server_front_ip)

    # Allow nrpe to listen on UDP port 5666
    iptables.add_monitor_chain()

    # Make nrpe-server startup stateful and restart
    x("/sbin/chkconfig --level 3 nrpe on")
    x("service nrpe restart")


def _install_nrpe_plugins():
    '''
    Install NRPE-plugins (to be executed remoteley) and SELinux-rules.

    '''
    # Install packages and their dependencies.
    _install_nrpe_plugins_dependencies()
    x("cp -p {0}lib/nagios/plugins_nrpe/* /usr/lib64/nagios/plugins/".format(constant.SYCO_PATH))

    # Set the sssd password
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")
    nrpe_config.replace("$(LDAPPASSWORD)", app.get_ldap_sssd_password())
    nrpe_config.replace("($LDAPURL)", config.general.get_ldap_hostname())

    # Change ownership of plugins to nrpe (from icinga/nagios)
    x("chmod -R 750 /usr/lib64/nagios/plugins/")
    x("chown -R nrpe:nrpe /usr/lib64/nagios/plugins/")

    # Set special permissions for Clam plugins
    # Note the suid setting.
    x("chown root:root /usr/lib64/nagios/plugins/check_clamscan")
    x("chown root:root /usr/lib64/nagios/plugins/check_clamav")
    x("chmod 4755 /usr/lib64/nagios/plugins/check_clamscan")
    x("chmod 4755 /usr/lib64/nagios/plugins/check_clamav")

    # Set SELinux roles to allow NRPE execution of binaries such as python/perl/iptables
    # Corresponding .te-files summarize rule content
    x("mkdir /var/lib/syco_selinux_modules")
    rule_path_list = list_plugin_files("/var/nagios/selinux_rules")
    for path in rule_path_list:
        x("cp {0}/*.pp /var/lib/syco_selinux_modules/".format(path))
    x("semodule -i /var/lib/syco_selinux_modules/*.pp")

    # Set MySQL password, if running MySQL.
    try:
        x("/usr/lib64/nagios/plugins/check_nrpe -H {0} -c get_services".format("127.0.0.1")).find("mysql")
        nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")
        nrpe_config.replace("$(SQLPASS)", app.get_mysql_monitor_password())
    except ValueError:
        pass


def _install_nrpe_plugins_dependencies():
    '''
    Install libraries/binaries that the NRPE-plugins depend on.

    '''
    # Dependency for check_rsyslog
    x("yum install -y MySQL-python")

    # Dependency for check_clamav
    x("yum install -y nagios-plugins-perl perl-Net-DNS-Resolver-Programmable sudo yum install perl-suidperl")

    # Dependency for check_clamscan
    x("yum install -y perl-Proc-ProcessTable perl-Date-Calc")

    # Dependency for check_ldap
    x("yum install -y php-ldap php-cli")

    # Dependency for hosts/firewall hardware checks
    host_config_object = config.host(net.get_hostname())
    if host_config_object.is_host() or host_config_object.is_firewall():

        # Create an installname and filenames
        install_dir = general.get_install_dir()

        # Download and install HP health monitoring package
        general.download_file(
            HP_HEALTH_URL, HP_HEALTH_FILENAME, md5=HP_HEALTH_MD5
        )
        x("yum install {0} -y".format(HP_HEALTH_FILENAME))

        # Let nrpe run hpasmcli
        nrpe_sudoers_file = scopen.scOpen("/etc/sudoers.d/nrpe")
        nrpe_sudoers_file.add("Defaults:nrpe !requiretty")
        nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/sbin/hpasmcli,/usr/lib64/nagios/plugins/check_hpasm")

        x("service hp-health start")


def list_plugin_files(path):
    '''
    Returns a full file-path for every plugin with the sub-path defined.

    '''
    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + path)
            if (os.access(plugin_path, os.F_OK)):
                yield plugin_path

