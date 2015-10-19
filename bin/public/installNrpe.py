#!/usr/bin/env python
"""
Install nrpe client

"""

import os

from general import x
import app
import config
import constant
import install
import iptables
import net
import scopen
import version


__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "daniel@cybercow.se"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.3"
__status__ = "Development"


PLG_PATH = "/usr/lib64/nagios/plugins/"

SCRIPT_VERSION = 3


def build_commands(commands):
    commands.add("install-nrpe-client", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")


def install_nrpe(args):
    """Install a hardened NRPE server, plugins and commands."""
    app.print_verbose("Installing nrpe")
    version_obj = version.Version("installNrpe", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nrpe(args)
    version_obj.mark_executed()


def _install_nrpe(args):
    """
    The nrpe installation is quite standard . Except that the stock NRPE.conf
    is replaced with a prepped one. Server only listens to this IP. Not super
    safe but better than nothing. Also, argument parsing is _disabled_.

    """
    # Initialize all used passwords at the beginning of the script.
    app.get_ldap_sssd_password()
    app.get_mysql_monitor_password()

    install.epel_repo()

    # Confusing that nagios-plugins-all does not really include all plugins
    x(
        "yum install -y nagios-plugins-all nrpe nagios-plugins-nrpe php-ldap "
        "nagios-plugins-perl perl-Net-DNS perl-Proc-ProcessTable"
        "perl-Date-Calc policycoreutils-python"
    )

    # Move object structure and prepare conf-file
    x("rm -rf /etc/nagios/nrpe.d")
    x("rm -rf /etc/nagios/nrpe.cfg")
    x("cp -r {0}syco-private/var/nagios/nrpe.d /etc/nagios/".format(constant.SYCO_USR_PATH))
    x("cp {0}syco-private/var/nagios/nrpe.cfg /etc/nagios/".format(constant.SYCO_USR_PATH))

    # Extra plugins installed
    _install_nrpe_plugins()

    # Allow only monitor to query NRPE
    monitor_server_front_ip = config.general.get_monitor_server_ip()
    app.print_verbose("Set monitor server: %s" % monitor_server_front_ip)
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.cfg")
    nrpe_config.replace("$(MONITORIP)", monitor_server_front_ip)

    # Set permissions for read/execute under nagios-user
    x("chown -R root:nagios /etc/nagios/")

    # Allow nrpe to listen on UDP port 5666
    iptables.add_nrpe_chain()
    iptables.save()

    # Make nrpe-server startup stateful and restart
    x("/sbin/chkconfig --level 3 nrpe on")
    x("service nrpe restart")


def _fix_selinux(type, filename):
    x("chcon -t {0} {1}{2}".format(type, PLG_PATH, filename))
    x("semanage fcontext -a -t {0} '{1}{2}'".format(type, PLG_PATH, filename))


def _install_nrpe_plugins():
    """Install NRPE-plugins (to be executed remoteley) and SELinux-rules."""
    # Install packages and their dependencies.
    _install_nrpe_plugins_dependencies()
    x("cp -p {0}lib/nagios/plugins_nrpe/* {1}".format(constant.SYCO_PATH, PLG_PATH))

    # Set the sssd password
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")
    nrpe_config.replace("$(LDAPPASSWORD)", app.get_ldap_sssd_password())
    nrpe_config.replace("$(LDAPURL)", config.general.get_ldap_hostname())
    nrpe_config.replace("$(SQLPASS)", app.get_mysql_monitor_password().replace("&","\&").replace("/","\/"))

    # Set name of main disk
    host_config = config.host(net.get_hostname())
    if host_config.is_guest():
        nrpe_config.replace("${MAINDISK}", "vda")
    elif host_config.is_firewall() or host_config.is_host():
        nrpe_config.replace("${MAINDISK}", "sda")

    # Change ownership of plugins to nrpe (from icinga/nagios)
    x("chmod -R 550 /usr/lib64/nagios/plugins/")
    x("chown -R nagios:nagios /usr/lib64/nagios/plugins/")

    # Set SELinux roles to allow NRPE execution of binaries such as python/perl.
    # Corresponding .te-files summarize rule content
    x("mkdir -p /var/lib/syco_selinux_modules")
    rule_path_list = list_plugin_files("/var/nagios/selinux_rules")
    for path in rule_path_list:
        x("cp {0}/*.pp /var/lib/syco_selinux_modules/".format(path))
    x("semodule -i /var/lib/syco_selinux_modules/*.pp")

    # Fix some SELinux rules on custom plugins.
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_disk")
    _fix_selinux("nagios_services_plugin_exec_t",   "check_ldap.php")
    _fix_selinux("nagios_services_plugin_exec_t",   "check_iptables.py")
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_clam*")
    # TODO??
    #_fix_selinux("nagios_unconfined_plugin_exec_t", "pmp-check-mysql*")
    #_fix_selinux("nagios_unconfined_plugin_exec_t", "farpayment_stats.py")
    #_fix_selinux("nagios_unconfined_plugin_exec_t", "rentalfront_stats.py")
    #_fix_selinux("nagios_unconfined_plugin_exec_t", "checkMySQLProcesslist.sh")
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_connections.pl")
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_procs.sh")
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_ulimit.py")
    _fix_selinux("nagios_unconfined_plugin_exec_t", "check_hpasm")

    # New in centos 6.7
    x("setsebool -P nagios_run_sudo 1")


def _install_nrpe_plugins_dependencies():
    """Install libraries/binaries that the NRPE-plugins depend on."""
    # Dependency for check_rsyslog
    x("yum install -y MySQL-python")

    # Dependency for check_clamav
    x("yum install -y nagios-plugins-perl perl-Net-DNS-Resolver-Programmable")
    x("yum install -y perl-suidperl")

    x("""cat > /etc/sudoers.d/nrpe << EOF
Defaults:nagios !requiretty
nagios ALL=NOPASSWD:{0}check_clamav
nagios ALL=NOPASSWD:{0}check_clamscan
nagios ALL=NOPASSWD:{0}check_disk
nagios ALL=NOPASSWD:{0}get_services
nagios ALL=NOPASSWD:{0}mysql/pmp-check-mysql-deleted-files
nagios ALL=NOPASSWD:{0}mysql/pmp-check-mysql-file-privs
EOF
""".format(PLG_PATH))

    # Dependency for check_clamscan
    x("yum install -y perl-Proc-ProcessTable perl-Date-Calc")

    # Dependency for check_ldap
    x("yum install -y php-ldap php-cli")

    # Dependency for check_iostat
    x("yum install -y sysstat")

    # Dependency for hosts/firewall hardware checks
    host_config_object = config.host(net.get_hostname())
    if host_config_object.is_host() or host_config_object.is_firewall():
        install.hp_repo()
        x("yum -y install hp-health")

        # Let nrpe run hpasmcli
    x("""cat >> /etc/sudoers.d/nrpe << EOF
nagios ALL=NOPASSWD:/sbin/hpasmcli
nagios ALL=NOPASSWD:{0}check_hpasm"
EOF
""".format(PLG_PATH))

    # Dependency for check_ulimit
    x("yum install -y lsof")

    # Set ulimit values to take affect after reboot
    x("printf '\n*\tsoft\tnofile\t8196\n*\thard\tnofile\t16392\n' >> /etc/security/limits.conf")

    # Kernel wont parse anything but read-only in sudoers. So chmod it.
    x("chmod 0440 /etc/sudoers.d/nrpe")


def list_plugin_files(path):
    """Returns a full file-path for every plugin with the sub-path defined."""
    if os.access(app.SYCO_USR_PATH, os.F_OK):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + path)
            if os.access(plugin_path, os.F_OK):
                yield plugin_path
