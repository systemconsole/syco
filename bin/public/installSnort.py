#!/usr/bin/env python
'''
Install of Snort

Snort is a NIDS that listens on network interface and if network traffic
matches any rule in the snort rules databas an alert in triggerd.

Snort is downloaded and bulid fron snort homepage. Snort rules that contains
all the rules nedded for snort to work are downloaded with key.

READ MORE
http://www.snort.org/assets/202/snort2931_CentOS63.pdf
http://wiki.aanval.com/wiki/Community:Snort_2.9.3.1_Installation_Guide_for_CentOS_6.3

'''


__author__ = "daniel@cybercowse, matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from general import x
from scopen import scOpen
import app
import config
import general
import version

SNORT_FILENAME="snort-2.9.4.tar.gz"
SNORT_URL="http://www.snort.org/downloads/2112"
SNORT_MD5="e79ee6b4fbb32edc5dfed2d7dfcc6813"

DAQ_FILENAME="daq-2.0.0.tar.gz"
DAQ_URL="http://www.snort.org/downloads/2103"
DAQ_MD5="a00855a153647df76d47f1ea454f74ae"

LIBNET_FILENAME="libnet-1.12.tgz"
LIBNET_URL="https://libdnet.googlecode.com/files/libdnet-1.12.tgz"
LIBNET_MD5="9253ef6de1b5e28e9c9a62b882e44cc9"

RULE_FILENAME="snortrules-snapshot-2931.tar.gz"
RULE_MD5="1254317ba5c51a6b8f2b5ba711eecfeb"

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
script_version = 1


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.

    """
    commands.add("install-snort",  install_snort, help="Install Snort.")


def download():
    """
    Download all files required by snort.

    Note: Should be modified to download files to install server.

    """

    installation_server = config.general.get_installation_server()

    rule_url = "http://{0}/files/{1}".format(
        installation_server, RULE_FILENAME)

    general.download_file(SNORT_URL, SNORT_FILENAME, md5=SNORT_MD5)
    general.download_file(DAQ_URL, DAQ_FILENAME, md5=DAQ_MD5)
    general.download_file(LIBNET_URL, LIBNET_FILENAME, md5=LIBNET_MD5)
    general.download_file(rule_url, RULE_FILENAME, md5=RULE_MD5)


def install_snort(args):
    '''
    Install and setup snort in client.
    And conencts the snort loggs

    '''
    download()
    _install_dependencies()
    _compile_snort()
    _create_user()
    _setup_config_and_rules()
    _setup_sysconfig()
    _setup_start_scripts()
    _setup_snort_bin()
    _setup_log_dir()

    x("mkdir -p /usr/local/lib/snort_dynamicrules")
    x('chown -R snort:snort /usr/local/lib/snort*')
    x('chmod -R 700 /usr/local/lib/snort*')

    #
    x("/etc/init.d/snort restart")


def _install_dependencies():
    x('yum install -y gcc gcc-c++ flex bison zlib zlib-devel libpcap libpcap-devel ' +
      'pcre pcre-devel libdnet libdnet-devel tcpdump libtool'
    )


def _compile_snort():
    _make('daq/', DAQ_FILENAME)
    _make('libnet/', LIBNET_FILENAME)
    _make('snort/', SNORT_FILENAME, '--enable-sourcefire')
    #x("libtool --finish /usr/local/lib/snort_dynamicpreprocessor")


def _make(build_dir, filename, compile_flags=""):
    '''
    Extract files from tar file defined by filename, and compile.

    '''
    compile_dir = app.INSTALL_DIR + build_dir

    x("rm -rf " + compile_dir)
    x("mkdir -p " + compile_dir)
    x("tar -C " + compile_dir + " -zxf " + app.INSTALL_DIR + filename)
    x("chown -R root:root %s" % compile_dir)

    # Move contents of extraxted folder to build folder.
    x("mv {0}/* {1}".format(_get_folder(compile_dir), compile_dir))

    x("./configure {0}".format(compile_flags), cwd=compile_dir)
    x("make", cwd=compile_dir)
    x("make install", cwd=compile_dir)


def _get_folder(folder):
    only_folder = None
    for dir in os.listdir(folder):
        if only_folder == None:
            only_folder = dir
        else:
            raise Exception("Folder {0} already found.".format(only_folder))
    return folder + only_folder


def _create_user():
    x("useradd snort -d /var/log/snort -s /sbin/nologin -c SNORT_IDS")
    x("groupadd snort")


def _setup_config_and_rules():
    # Removing content /etc/snort-rules
    x("mkdir -p /etc/snort/")
    x("rm -rf /etc/snort/*")

    # Setup snort config and rules
    x("cp {0}/etc/* /etc/snort".format(app.INSTALL_DIR + 'snort'))
    x("tar -C /etc/snort -zxvf {0}{1}".format(app.INSTALL_DIR, RULE_FILENAME))

    x("cp -f {0}var/snort/snort.conf /etc/snort/".format(app.SYCO_PATH))
    x("echo '#Black list' > /etc/snort/rules/black_list.rules")
    x("echo '#White list' > /etc/snort/rules/white_list.rules")

    x("chown -R snort:snort /etc/snort/")
    x("find /etc/snort/ -type d -print0 | xargs -0 chmod 700")
    x("find /etc/snort/ -type f -print0 | xargs -0 chmod 600")


def _setup_start_scripts():
    x('cp -f {0}var/snort/snort-init.d /etc/init.d/snort'.format(app.SYCO_PATH))
    x("chown snort:snort /etc/init.d/snort")
    x("chmod 700 /etc/init.d/snort")

    # Setup init.d and autostart
    x("chkconfig --add snort")


def _setup_sysconfig():
    x('cp -f {0}var/snort/snort-sysconfig /etc/sysconfig/snort'.format(app.SYCO_PATH))
    x("chown snort:snort /etc/sysconfig/snort")
    x("chmod 700 /etc/sysconfig/snort")


def _setup_snort_bin():
    x("ln -s /usr/local/bin/snort /usr/bin/snort")
    x("ln -s /usr/local/bin/snort /usr/sbin/snort")
    x("chmod 700 /usr/bin/snort")
    x("chmod 700 /usr/sbin/snort")


def _setup_log_dir():
    # Create log dir
    x('mkdir -p /var/log/snort')
    x('chown snort:snort /var/log/snort')
    x('chmod 700 /var/log/snort')
