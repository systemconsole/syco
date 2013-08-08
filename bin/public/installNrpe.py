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
import ConfigParser


__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Elis Kullberg"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.1"
__status__ = "Development"


HP_HEALTH_FILENAME="hp-health-9.1.0.42-54.rhel6.x86_64.rpm"
HP_HEALTH_URL="http://downloads.linux.hp.com/SDR/psp/RedHatEnterpriseES/6.0/packages/x86_64/{0}".format(HP_HEALTH_FILENAME)
HP_HEALTH_MD5="0bc2a9932c3080829a96ab7bb4727089"


SCRIPT_VERSION = 2


def build_commands(commands):
    commands.add("install-nrpe-client", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")
    commands.add("update-nrpe-config", update_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")


def install_nrpe(args):
    '''
    Install a hardened NRPE server (to be run on every host), plugins and commands.

    '''
    app.print_verbose("Installing nrpe")
    version_obj = version.Version("installNrpe", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nrpe(args)
    version_obj.mark_executed()


def update_nrpe(args):
    '''
    Update the nrpe config with new settings for nrpe deamon.
    '''
    #Reading config file
    config = ConfigParser.ConfigParser()
    config.read('/opt/syco/usr/syco-private/var/nagios/hosts_nrpe_config.cfg')
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")

    #Getting setting for host and modyfying command.cfg
    try:        
        for name, value in config.items(net.get_hostname()):
            nrpe_config.replace("^command\[" + name + "\].*", value)
            print '  %s = %s' % (name, value)
        #Setting correct SQL password to config
        nrpe_config.replace("$(SQLPASS)", app.get_mysql_monitor_password().replace("&","\&").replace("/","\/"))
    
    #No custom enteries for host passing
    except Exception: 
        pass

    #Restart nrpe so changes take effect    
    x("/etc/init.d/nrpe restart")


def _install_nrpe(args):
    '''
    The nrpe installation is quite standard - except that the stock NRPE.conf is replaced with a prepped one.
    Server only listens to this IP. Not super safe but better than nothing. Also, argument parsing is _disabled_.

    '''
    # Initialize all passwords at the beginning of the script.
    app.get_ldap_sssd_password()
    app.get_mysql_monitor_password()

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
    iptables.add_nrpe_chain()
    iptables.save()

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

    #copy in extra plugins.
    x("cp -r /opt/syco/var/nrpe/* /usr/lib64/nagios/plugins")

    # Set the sssd password
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")
    nrpe_config.replace("$(LDAPPASSWORD)", app.get_ldap_sssd_password())
    nrpe_config.replace("($LDAPURL)", config.general.get_ldap_hostname())

    # Change ownership of plugins to nrpe (from icinga/nagios)
    x("adduser nrpe")
    x("chmod -R 750 /usr/lib64/nagios/plugins/")
    x("chown -R nrpe:nrpe /usr/lib64/nagios/plugins/")

    # Set SELinux roles to allow NRPE execution of binaries such as python/perl/iptables
    # Corresponding .te-files summarize rule content
    x("mkdir -p /var/lib/syco_selinux_modules")
    rule_path_list = list_plugin_files("/var/nagios/selinux_rules")
    for path in rule_path_list:
        x("cp {0}/*.pp /var/lib/syco_selinux_modules/".format(path))
    x("semodule -i /var/lib/syco_selinux_modules/*.pp")

    # Set MySQL password, if running MySQL.
    nrpe_config = scopen.scOpen("/etc/nagios/nrpe.d/common.cfg")
    nrpe_config.replace("$(SQLPASS)", app.get_mysql_monitor_password().replace("&","\&").replace("/","\/"))


def _install_nrpe_plugins_dependencies():
    '''
    Install libraries/binaries that the NRPE-plugins depend on.

    '''
    # Dependency for check_rsyslog
    x("yum install -y MySQL-python")

    # Dependency for check_clamav
    x("yum install -y nagios-plugins-perl perl-Net-DNS-Resolver-Programmable sudo yum install perl-suidperl")

    nrpe_sudoers_file = scopen.scOpen("/etc/sudoers.d/nrpe")
    nrpe_sudoers_file.add("Defaults:nrpe !requiretty")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/check_clamav")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/check_clamscan")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/check_disk")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/get_services")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/mysql/pmp-check-mysql-deleted-files")
    nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/mysql/pmp-check-mysql-file-privs")

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

        # Remove their evil crontab
        x("rm -f /etc/cron.d/hp-health")

        # Let nrpe run hpasmcli
        nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/sbin/hpasmcli")
        nrpe_sudoers_file.add("nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/check_hpasm")

        x("service hp-health start")


    # Kernel wont parse anything but read-only in sudoers. So chmod it.
    x("chmod 0440 /etc/sudoers.d/nrpe")


def list_plugin_files(path):
    '''
    Returns a full file-path for every plugin with the sub-path defined.

    '''
    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + path)
            if (os.access(plugin_path, os.F_OK)):
                yield plugin_path

