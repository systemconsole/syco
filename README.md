System Console
==============

System Console (syco) is a collection of installation and management
scripts that helps a sysop to administrate his linux servers.

Installation
------------

Clone the repo from github. It's preferred to install it in the /opt folder.
    cd /opt
    git clone https://github.com/systemconsole/syco.git

Setup a proper configuration file, for example
    ln -s  /opt/syco/usr/example/etc/install.cfg /opt/syco/etc/install.cfg

Add private/customized scripts.
    cd /opt/syco/usr
    git clone https://github.com/systemconsole/syco-template.git

Let syco install it self.
    /opt/syco/bin/syco.py install-syco

Now you can run the syco script from anywhere, for example.
    cd /root
    syco hardening

If you are member of the syco team, use this to push things back to github.
    ssh-keygen -t rsa
    cat ~/.ssh/id_rsa.pub
    # Insert the output into www.github.com.
    git clone git@github.com:arlukin/syco.git

The flow of the "syco remote-install"
------------------------------------

* Download syco from git
* On VirtualHost "syco install-local", this should be the only command that
  needs to be executed by hand. The following commands will be executed
  automatically.
    * "syco hardening"
    * "syco install-kvmhost"
    * "syco install-fo-tp-install", will install InstallGuest
        * On InstallGuest "syco hardening"
        * On InstallGuest "syco install-cobbler"
        * On InstallGuest "syco remote-install"
            * Look for alive hosts defined in install.cfg
            * Run "syco remote-install xx" on the host alive.
            * Continue until "remote-install" has been executed on all servers.
    * "syco install-guests"
        * Install 2 guests on VirtualHost Web and Mysql



