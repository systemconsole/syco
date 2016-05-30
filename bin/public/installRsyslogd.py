#!/usr/bin/env python
"""
Install of rsyslog server

Install rsyslog server and setup tls server on tcp port 514 and unencrypted
loggning on udp 514.

SOME ROUTINES
* All logs from all servers/clients are stored on file.
* Logs on file are compressed everyday with bzip for best compression. Those
  files are supposed to be stored forever.
* All files stored are deleted after 90 days.

NOTE: Client certs need to be regenerated once year.

LOGGING TO
Logs are saved to a file structure in
/var/log/remote/year/month/day/servername

NEW CERTS
$ syco install-rsyslogd-newcerts
Installation can generate/regenerate certs and CA for rsyslogd server. Certs are stored in
/etc/pki/rsyslog folder.

Clients generate their own certs on demand.

CONFIG FILES
rsyslog.d config files are located in syco/var/rsyslog/ folder. Template used
for generating certs are located in /syco/var/rsyslog/template.ca and
template.server

READING
http://www.rsyslog.com/doc
http://www.rsyslog.com/doc/rsyslog_conf.html
http://www.rsyslog.com/doc/rsyslog_tls.html

https://access.redhat.com/knowledge/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/ch-Viewing_and_Managing_Log_Files.html

"""

__author__ = "daniel@cybercow.se, matte@elino.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from config import get_servers
from general import get_install_dir, install_packages
from general import x
from scopen import scOpen
import app
import config
import installLogrotate
import iptables
import net
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.

    """
    commands.add("install-rsyslogd",          install_rsyslogd,   help="Install Rsyslog server.")
    commands.add("uninstall-rsyslogd",        uninstall_rsyslogd, help="Uninstall rsyslog server and all certs on the server.")
    commands.add("install-rsyslogd-newcerts", rsyslog_newcerts,   help="Generates new ca cert and key.")


def install_rsyslogd(args):
    """
    Install rsyslogd on the server.

    """
    app.print_verbose("Install rsyslogd.")
    version_obj = version.Version("InstallRsyslogd", SCRIPT_VERSION)
    version_obj.check_executed()

    # Installing packages
    install_packages("rsyslog rsyslog-gnutls gnutls-utils")

    # Autostart rsyslog at boot
    x("chkconfig rsyslog on")

    # Generation new certs if no certs exsists
    if not os.path.exists('/etc/pki/rsyslog/ca.crt'):
        rsyslog_newcerts(args)

    _setup_rsyslogd()

    # Add iptables chains
    iptables.add_rsyslog_chain("server")
    iptables.save()

    # Restarting service
    x("service rsyslog restart")

    install_compress_logs()

    # Configure logrotate
    installLogrotate.install_logrotate(args)

    version_obj.mark_executed()


def _setup_rsyslogd():
    """
    Setup rsyslogd config files.

    """
    x("cp -f /opt/syco/var/rsyslog/rsyslogd.conf /etc/rsyslog.conf")
    x("chmod 640 /etc/rsyslog.conf")

    sc = scOpen("/etc/rsyslog.conf")
    sc.replace('${SERVERNAME}', '{0}.{1}'.format(
        net.get_hostname(), config.general.get_resolv_domain())
    )
    sc.replace('${DOMAIN}', config.general.get_resolv_domain())

    # Setup folder to store logs from clients.
    app.print_verbose("CIS 5.2.4 Create and Set Permissions on rsyslog Log Files")
    app.print_verbose("  Will not create individual files.")
    x("mkdir -p /var/log/rsyslog/")
    x("chown root:root /var/log/rsyslog/")
    x("chmod 700 /var/log/rsyslog/")
    x("restorecon /var/log/rsyslog/")


def rsyslog_newcerts(args):
    """
    Generate new tls certs for rsyslog server

    NOTE: This needs to be executed once a year.

    """
    x("mkdir -p /etc/pki/rsyslog")

    # Copy certs template
    template_ca = "{0}template.ca".format(get_install_dir())
    x("cp -f /opt/syco/var/rsyslog/template.ca {0}".format(template_ca))

    hostname = "{0}.{1}".format(net.get_hostname(), config.general.get_resolv_domain())
    _replace_tags(template_ca, hostname)

    # Making CA
    x("certtool --generate-privkey --outfile /etc/pki/rsyslog/ca.key")
    x("certtool --generate-self-signed --load-privkey /etc/pki/rsyslog/ca.key "+
      "--outfile /etc/pki/rsyslog/ca.crt " +
      "--template {0}".format(template_ca)
    )

    # Copy server template and cert/key generator script
    target_template = '/etc/pki/rsyslog/template.server'
    x("cp -f /opt/syco/var/rsyslog/template.server {0}".format(target_template))
    _replace_tags(target_template, fqdn)

    # New generator script used by clients directly
    generator_script = "syco-gen-rsyslog-client-keys.sh"
    x("cp -f /opt/syco/var/rsyslog/{0} /etc/pki/rsyslog/".format(generator_script))
    x("chmod 700 /etc/pki/rsyslog/{0}".format(generator_script))


def _replace_tags(filename, fqdn):
    """
    Replace all tags in template files with apropriate values.

    """
    sc = scOpen(filename)
    sc.replace('${ORGANIZATION}', config.general.get_organization_name())
    sc.replace('${UNIT}', config.general.get_organizational_unit_name())
    sc.replace('${LOCALITY}', config.general.get_locality())
    sc.replace('${STATE}', config.general.get_state())
    sc.replace('${COUNTRY}', config.general.get_country_name())
    sc.replace('${CN}', fqdn)
    sc.replace('${DNS_NAME}', fqdn)
    sc.replace('${EMAIL}', config.general.get_admin_email())
    sc.replace('${SERIAL}', _get_serial())


def _get_serial():
    """
    Return a unique (autoinc) serial number that are used in template files.

    """
    _get_serial.serial = _get_serial.serial + 1
    return str(_get_serial.serial)
_get_serial.serial = 0


def uninstall_rsyslogd(args):
    """
    Remove Rsyslogd server from the server

    """
    app.print_verbose("Uninstall Rsyslogd SERVER")
    x("yum erase rsyslog rsyslog-gnutls gnutls-utils")
    x("rm -rf /etc/pki/rsyslog")
    version_obj = version.Version("InstallRsyslogd", SCRIPT_VERSION)
    version_obj.mark_uninstalled()


def install_compress_logs():
    """
    Install a script that compresses all 1 day old remote logs.

    """
    # Script should be executed once every day.
    fn = "/etc/cron.daily/compress-logs.sh"
    x("cp -f {0}var/rsyslog/compress-logs.sh {1}".format(app.SYCO_PATH, fn))
    x("chmod +x {0}".format(fn))

