#!/usr/bin/env python
"""
Install Fareoffice.

This script installs Fareoffice, the php-system. If the script is executed on a
server which has already been set into production, it will strive to fix
potential errors without interferring with the uptime more than necessary.

It needs to be executed with the -f (force) flag when executed a secondary
time.

"""

__author__ = "daniel@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
from time import sleep

import app
import nfs
from general import x, shell_run
from scopen import scOpen
import version


SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.

    """
    commands.add("install-fareoffice", install_fareoffice, help="Install fareoffice.")


def install_fareoffice(args):
    """
    Fareoffice installation

    """
    app.print_verbose("Install Fareoffice version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("Installfareoffice", SCRIPT_VERSION)
    version_obj.check_executed()

    _disable_selinux()
    _yum_install()
    _install_syco_github_sshkey()
    _clone_repos()
    _create_folders()
    _create_log_folder()
    _setup_sudo()
    _setup_httpd_conf()
    _setup_nfs()
    _setup_rsyncd()
    _install_wkhtmltopdf()
    _set_to_master_or_slave()
    _relink_dynamic_in_usr_folder()
    _deploy_code()
    _set_permissions()

    version_obj.mark_executed()


def _disable_selinux():
    app.print_verbose("Disable selinux, WebRes is not compatible with selinux.")
    x("echo 0 > /selinux/enforce")
    scOpen("/etc/selinux/config").replace(
        "SELINUX=enforcing", "SELINUX=permissive"
    )


def _yum_install():
    app.print_verbose("Install yum packages.")
    x("yum -y install php php-mysql php-soap nfs-utils rsync php-xml vsftpd")


def _install_syco_github_sshkey():
    app.print_verbose("Install sshkey to be able to connect to github.")

    if not os.path.exists('/root/.ssh/id_rsa'):
        # Syco might have installed a .ssh file, that are invalid.
        if os.path.exists('/root/.ssh'):
            x("rm /root/.ssh")
        x("ssh-keygen -t rsa -N '' -f /root/.ssh/id_rsa")

    x("cp -f " + SYCO_FO_PATH + "var/ssh/id_rsa_syco_github /root/.ssh")
    x("cp -f " + SYCO_FO_PATH + "var/ssh/id_rsa_syco_github.pub /root/.ssh")

    x("touch /root/.ssh/config")

    scOpen("/root/.ssh/config").remove("Host github.com")
    scOpen("/root/.ssh/config").remove("Hostname github.com")
    scOpen("/root/.ssh/config").remove("IdentityFile /root/.ssh/id_rsa_syco_github")

    scOpen("/root/.ssh/config").add("Host github.com")
    scOpen("/root/.ssh/config").add("Hostname github.com")
    scOpen("/root/.ssh/config").add("IdentityFile /root/.ssh/id_rsa_syco_github")
    x("chmod 600 /root/.ssh/*")
    x("chown root:root /root/.ssh/*")


def _git_clone(repo, folder, branch=""):
    if not os.path.exists(folder + ".git"):
        if branch:
            branch = "--branch " + branch

        repo = "git@github.com:fareoffice/" + repo
        shell_run(
            "git clone %s %s %s" % (branch, repo, folder),
            events = {
                'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
            }
        )


def _create_folders():
    x("mkdir -p /opt/RootLive/DynamicMaster")
    x("mkdir -p /opt/RootLive/DynamicSlave")
    x("mkdir -p /opt/RootLive/Site/DistEnterpriseProduction/Temp/Cache/smarty/templates_c")
    x("mkdir -p /opt/RootLive/Site/DistEnterpriseRelease/Temp/Cache/smarty/templates_c")


def _clone_repos():
    app.print_verbose("Clone repose from github.")

    # TODO should take the master branch when totally merged with master B.
    _git_clone("fareoffice",             "/opt/RootLive/")
    _git_clone("fareoffice-sycochuck",   "/opt/RootLive/Site/sycochuck-production")
    _git_clone("fareoffice-sysop",       "/opt/RootLive/Site/DistSysOpProduction")
    _git_clone("fareoffice-hertz",       "/opt/RootLive/Site/DistHertzProduction")
    _git_clone("fareoffice-webpage",     "/opt/RootLive/Site/DistFareofficeProduction")

    x("mkdir -p /tmp/fareoffice")
    _git_clone("fareoffice-enterprise",  "/tmp/fareoffice/DistEnterpriseProduction")


def _remove_file(file_name):
    """Remove existing files."""
    if os.path.lexists(file_name):
        x("rm %s" % file_name)


def _create_log_folder():
    app.print_verbose("Create log folders.")
    _remove_file("/opt/RootLive/Log")
    _remove_file("/var/log/fareoffice/httpd")

    x("mkdir -p /var/log/fareoffice/php")
    x("ln -s /var/log/fareoffice /opt/RootLive/Log")
    x("ln -s /var/log/httpd      /var/log/fareoffice/")


def _setup_sudo():
    x("/opt/RootLive/bin/setup-sudo")


def _set_permissions():
    x("/opt/RootLive/bin/setup-permissions --all")


def _setup_httpd_conf():
    x("/opt/RootLive/bin/setup-httpd-conf")


def _setup_nfs():
    app.print_verbose("Remove nfs exports")
    nfs.remove_export("log")
    nfs.remove_export("DynamicMaster")
    nfs.remove_iptables_rules()
    nfs.disable_services_autostart()

    app.print_verbose("Setup nfs exports")
    nfs.add_export("log",           "/opt/RootLive/log")
    nfs.add_export("DynamicMaster", "/opt/RootLive/DynamicMaster")
    nfs.add_iptables_rules()
    nfs.restart_services()
    nfs.enable_services_autostart()


def _setup_rsyncd():
    app.print_verbose("Restart rsync daemon")
    x("killall rsync")
    sleep(1)
    x("/usr/bin/rsync --daemon --config=/opt/RootLive/etc/rsync/rsyncd.conf")

    app.print_verbose("Autostart rsync daemon")
    f = scOpen("/etc/rc.local")
    f.remove("rsync")
    f.add(
        "/usr/bin/rsync --daemon " +
        "--config=/opt/RootLive/etc/rsync/rsyncd.conf "
    )


def _install_wkhtmltopdf():
    """
    Software to convert html to pdf

    """
    x("/opt/RootLive/bin/setup-wkhtmltopdf")


def _set_to_master_or_slave():
    """
    If already a slave, "remount" slave functionality otherwise set to master.

    """
    if os.path.exists("/opt/RootLive/etc/IsSlaveServer"):
        ip = open("/opt/RootLive/etc/IsSlaveServer").readline()
        x("/opt/RootLive/bin/setup-as-slave %s -f" % ip)
    else:
        x("/opt/RootLive/bin/setup-as-master -f")


def _relink_dynamic_in_usr_folder():
    app.print_verbose("Relink dynamic in dist folder.")

    # Might fail if /opt/RootLive/Dynamic is not initialized correctly.
    for distro in os.listdir("/opt/RootLive/Site/"):
        usr_dyn_path = "/opt/RootLive/Site/%s/Dynamic" % distro
        dyn_path = "/opt/RootLive/Dynamic/%s" % distro
        app.print_verbose("  %s (check)" % usr_dyn_path)
        _remove_file(usr_dyn_path)
        
        app.print_verbose("  %s (Relink dynamic)" % usr_dyn_path)
        x("mkdir -p /opt/RootLive/Dynamic/%s" % distro)
        x("ln -s %s %s" % (dyn_path, usr_dyn_path))



def _deploy_code():
    app.print_verbose("Deploy code.")
    # Copy the Static and Content to the correct locations like sycochuck does.
    x("cp -R /tmp/fareoffice/DistEnterpriseProduction/Static  /opt/RootLive/Site/DistEnterpriseProduction/Static")
    x("cp -R /tmp/fareoffice/DistEnterpriseProduction/Content /opt/RootLive/Site/DistEnterpriseProduction/Dynamic/Content")
    x("cp -R /tmp/fareoffice/DistEnterpriseProduction/Static  /opt/RootLive/Site/DistEnterpriseRelease/Static")
    x("cp -R /tmp/fareoffice/DistEnterpriseProduction/Content /opt/RootLive/Site/DistEnterpriseRelease/Dynamic/Content")

    # Set Production mode in WebInit
    x("sed -i \"s/define('DEVELOP', TRUE);/define('DEVELOP', FALSE);/\" " +
      "/opt/RootLive/Site/DistEnterpriseProduction/Static/PhpInc/WebInit.php ")
    x("sed -i \"s/define('DEVELOP', TRUE);/define('DEVELOP', FALSE);/\" " +
      "/opt/RootLive/Site/DistEnterpriseRelease/Static/PhpInc/WebInit.php ")
