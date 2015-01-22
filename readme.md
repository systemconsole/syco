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

        ln -s  /opt/syco/usr/mod-template/etc/install.cfg /opt/syco/etc/install.cfg

Add private/customized scripts, for example

        cd /opt/syco/usr
        git clone https://github.com/systemconsole/syco-private.git

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

Contributing to syco
--------------------

        # Prepare repos
        https://github.com/<username>/syco.git
        git remote add devloper https://github.com/developer/syco.git
        git remote add upstream https://github.com/systemconsole/syco.git
        git fetch
        git branch -r

        # Create local copy of upstream/version-0.2.6
        git checkout upstream/version-0.2.6
        git checkout -b installRsyslog

        # Working on my feature
        git commit -am"Commit 1"
        git commit -am"Commit 2"
        git commit -am"Commit 3"
        git commit -am"Commit 4"
        git push developer -- instalRsyslog

        # Get all the latest branches and their code.
        git fetch upstream

        # Merge your feature
        git merge upstream/version-0.2.7

        # Squash all your commits into one commit.
        git reset upstream/version-0.2.7
        git add .
        git add -u .
        git commit

        # Push back to your own github repo.
        git push developer

        # Login to github and create a pull request.


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



Unit test 
---------

        Download and intsall virtualbox (https://www.virtualbox.org/wiki/Downloads)
        Download and intsall vagrant (https://www.vagrantup.com/downloads.html)
        vagrant box add mattiashem/syco_prep_centos6
        vagrant up
        vagrant ssh
        sudo rpm -Uhv http://mirrors.se.eu.kernel.org/fedora-epel/6/x86_64/epel-release-6-8.noarch.rpm
        sudo yum install python-pip
        sudo yum install python-devel
        sudo pip install pytest coverage
        /opt/syco/bin/test-all