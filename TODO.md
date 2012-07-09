Version 0.2.3
-------------
* See syco-private step 1-6

Version 0.3
-----------
* installBind
  Remove fareoffice relation.
  /Users/dali/mount/fo-tp-dalitst/syco/var/dns/fareonline.net:
* Test bind installation with https://www.ultratools.com

Version 0.4
-----------
* installNagios
* http://en.wikipedia.org/wiki/OSSIM
  http://alienvault.com/products/unified-siem
* Check
  http://pve.proxmox.com/wiki/File:Screen-startpage-with-cluster.png

Version 3.9 (iptables)
----------------------
* Looks like iptables allows port 80 to all servers. Can connect to
  offical yum repo servers.
* Separate rules for eth0 and eth1, br0 and br1?
* Create the allowed_tcp/udp directly under INPUT to first filter on tcp or udp.
  This will optimize all rules by "50%".
* Don't try to delete chains, when they don't exist. To remove the error message from iptables.
* Iptables are blocking on ip numbers. If a domain name is used, it will cache
  the ip-number. We need to do something about this.
* iptables-setup
  http://lonesysadmin.net/2007/10/29/how-to-install-a-tftp-server-on-red-hat-enterprise-linux/
  # /etc/sysconfig/iptables-config
  # Add IPTABLES_MODULES="ip_conntrack_tftp"
* Add recent http://www.snowman.net/projects/ipt_recent/
  http://www.frozentux.net/iptables-tutorial/scripts/recent-match.txt
* SSH to the server should only be allowed from certain ips.
* Write fireall/router iptables forwarding script. To replace clavister

Version 4
---------
* Add right licence to all files. Add licence file to root folder.
* remote-install-ssh-keys (on all syco-servers)
* Try --extra-args "console=ttyS0,115200 text headless"
  on virt-install.
  http://serverfault.com/questions/257962/kvm-guest-installed-from-console-but-how-to-get-to-the-guests-console

Monitor
-------
* Use aureport to read auditd log files.
  http://dgz.dyndns.org/mediawiki/index.php/(RHEL)_HOWTO_configure_the_auditing_of_the_system_(auditd)#Using_aureport
* Check this http://snorby.org/
* Check cpu sensors (temp), IPMI??
* Build report tool to check swap memory.
  A webserver should never ever have to swap, as swapping increases the latency
  of each request beyond a point that users consider "fast enough".
* Monitor cpu temp
* Check that no swap exists on the kvm hosts.
* Monitors hardware, snmp??

Hardening
---------
* Write a script that runs syco audit-cis every day/hour and emails the diff
  between last run and current run to sysop.
* Setup  /etc/hosts.allow and ate /etc/hosts.deny  from iptables script.
  # echo "ALL: ALL" >> /etc/hosts.deny
* Read doc for centos 6
  http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/
  http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Security_Guide/index.html
* Harden kickstart files according to
  http://kickstart-maker.googlecode.com/svn-history/r20/trunk/kickstart.template
  http://kickstart-maker.googlecode.com/svn-history/r20/trunk/post/
* Harden according to, or later version.
  http://www.nsa.gov/ia/_files/os/redhat/rhel5-guide-i731.pdf
* http://www.sans.org/score/checklists/linuxchecklist.pdf
* http://serverfault.com/questions/89923/what-tool-or-scripts-do-you-use-to-audit-a-linux-box
* Harden, remove/disable these services
  hplip,isdn,kudzu,xfs,nfs,xinetd,rhnsd,kdump,readahead_later,messagebus,haldaemon,apm
* Add user used by syco, so it don't need to use root. Then prevent root ssh login.
  user --name=syco --uid=500 --groups=wheel,root --password=nothingspecial
* Immunize all config files with "chattr +i xx", files that shouldn't be modified by anyone.
* semanage on all files we are using chcon on.
* Mask password that are written to the stdout.
* Add epel repo to fo-tp-install
  repo --name=lepel       --baseurl=http://10.0.0.1:81/yum-repos/epel/i386
  rpm -Uhv http://download.fedora.redhat.com/pub/epel/6/x86_64/epel-release-6-5.noarch.rpm
* Secure SSH?
  http://serverfault.com/questions/334448/why-is-ssh-password-authentication-a-security-risk?newsletter=1&nlcode=30229%7c0cb7

Log-server
---------

http://wiki.rsyslog.com/index.php/Rsyslog_on_CentOS_success_story
http://loganalyzer.adiscon.com/
http://www.linuxjournal.com/content/centralized-logging-web-interface
http://www.howtoforge.com/building-a-central-loghost-on-centos-and-rhel-5-with-rsyslog
http://aaronwalrath.wordpress.com/2010/09/02/set-up-rsyslog-and-loganalyzer-on-centos-linux-5-5-for-centralized-logging/
http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch05_:_Troubleshooting_Linux_with_syslog
http://www.syslog.org/wiki/Main/LogAnalyzers
http://serverfault.com/questions/239401/splunk-is-fantastically-expensive-what-are-the-alternatives
http://serverfault.com/questions/62687/alternatives-to-splunk
http://stackoverflow.com/questions/183977/what-commercial-and-open-source-competitors-are-there-to-splunk/
http://www.syslog.org/wiki/Main/LogAnalyzers

Bra att logga till både rsyslog och syslogd-ng?

Remote-install
--------------
* install-guests "virsh list" just print a .
* remote-install should log all output to file, one for each server/thread.
  http://docs.python.org/library/logging.html#logging-to-multiple-destinations
  http://stackoverflow.com/questions/616645/how-do-i-duplicate-sys-stdout-to-a-log-file-in-python
* Looks like remote-install are doing multiple installations to the same server
  at the same time. Maybe starting multiple threads for each server.
* syco remote-install, should loop and wait for all clients to become alive.
  Then run all commands on them.
* The guests should use the repos from the cobbler server.
* The guest should be locally "firewalled" to not be able to reach out to
  anything more then they need.
* Run "remote-install-deamon" on cobbler server.
* The remote-install deamon should check for changes in install.cfg.
* Add all output from syco to a log file.
* Add "syco remote-install" in kickstart for fo-tp-install

Refactoring / Stability
-----------------------
* mail_relay.domain_name should be mail_relay.hostname
* mysql.primary_master should be mysql.primary_master.servername
* Add timestamp to the prompt, for better logging.
# Rename general.popen to x (as in eXecute)
* Change so first virtualhost uses installserver as repo server after installation.
* Refactoring of password and passwordStore
* Use properties instead of getters in config
* install-mysql-replication should wait until users are installed on primary database.
* restorecon -R -v /home/$ACCOUNT/.ssh
* cobbler reposync has problems when selinux is enabled.
  See tmp/test-cobbler-sync.sh

KVM
---
* Add --cpuset=auto thingy to cobbler installed guests, to get the right NUMA.
* Setup console
  http://www.cyberciti.biz/faq/linux-kvm-redirecting-freebsd-virtual-machines-console-to-aserialport/
* http://www.linux-kvm.org/page/Tuning_KVM
* http://www.linux-kvm.org/page/Tuning_Kernel
* http://www.linux-kvm.org/page/HOWTO

Rentalfront Development enviornment
-----------------------------------
* installHudson
* installSonar

Version 5
---------
* Anything that is useful http://www.lesswatts.org/?
* Anything good on this site?
  http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=1
  http://docs.fedoraproject.org/en-US/Fedora/15/html/Deployment_Guide/index.html
* Add something from this
  http://serverfault.com/questions/322997/how-do-you-make-it-obvious-you-are-on-a-production-system
* Add reviewboard.com to vcs server???
* Check "gerrit" code review software and implement on vcs server.
* Configure openvpn for ubuntu https://help.ubuntu.com/10.04/serverguide/C/openvpn.html
* configure installCA, merge with CA stuff in installOpenVpn?
* installOpenvpn, has the client openvpn certs a unique common name?
* installOpenvpn, harden openvpn, jailroot, ta.key, Unprivileged mode
  http://openvpn.net/index.php/open-source/documentation/howto.html#security
* See all todos in installMysql
* User can use syco with a console/shell behaviour. Much like mysql, virsh,
  asadmin console. The user can login to a remote host and run local commands.
  http://docs.python.org/library/cmd.html
  http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/
* Test ZFS?


LDAP
----
# Enable sudo for LDAP users.
  http://electromech.info/sudo-ldap-with-rhds-linux-open-source.html
# Setup SSSD
# Setup password policy
* Setup replication, to get master-master working?
* Add  or similiar
  http://en.wikipedia.org/wiki/LDAP_Account_Manager
  http://en.wikipedia.org/wiki/PhpLDAPadmin
* Setup kickstart to use LDAP
  http://web.archiveorange.com/archive/v/YcynVMg4S203uVyu3ZFc
* Two-factor auth with http://www.wikidsystems.com/ or something else.
* Two-factor SSH with YubiKey on CentOS 5.6
  http://www.grennan.com/?p=170
  http://code.google.com/p/yubico-pam/wiki/ReadMe
  http://www.linuxforu.com/2011/08/setip-two-factor-authentication-using-openotp/
* 2-factor auth
  http://www.wikidsystems.com/
  http://www.wikidsystems.com/support/wikid-support-center/how-to/how-to-add-two-factor-authentication-to-openldap-and-freeradius
* Add Kerberos
* check_password pwdChecker http://open.calivia.com/projects/openldap/
* Add Radius?
  http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch31_:_Centralized_Logins_Using_LDAP_and_RADIUS#Configuring_RADIUS_for_LDAP


  Buy?
  https://store.yubico.com/
  http://nordicedge.com/yubikey?_kk=yubikey&_kt=719e84e7-3154-4db0-ae0d-824db7f359fc&gclid=CLiZvv6Y6qoCFUcYzQodDUgIOw
  http://www.yubico.com/fedora-uses-yubikey-for-strong-two-factor-authentication-

  http://www.yubico.com/radius
* two-factor - http://www.rcdevs.com/demos/#
* Port-knocking
  http://ubuntuforums.org/showthread.php?t=812573
* Use SASL?
* Use KERBEROS?
* Use Radius?
* Store hosts in ldap?
* Backup the LDAP database. Primary the passwords need backup.
* Install secondary "read-only" ldap server.
* Read for more features
  http://www.openldap.org/doc/admin24/OpenLDAP-Admin-Guide.pdf
* nfs mount fo-tp-file?
* vpn create sync with ldap users.

Other
-----
* Check articles http://articles.slicehost.com/sitemap
* Any good info here ? http://crunchtools.com/articles/
* Add to git server
  https://bitbucket.org/sdorra/scm-manager/wiki/Home
* Setup dhcp device in /etc/sysconfig/dhcpd for installDhcp


On Call (Linux Ocean?)
----------------------
* Surrvelience service, an sms is sent when somehting is wrong. The on call guy
  needs to report back to a system, that the error is notified. Otherwiese
  a new sms is sent to the second on call guy.

Glassfish
----------

* Set glassfish user to not be able to login in passwd.
  glassfish:x:200:200::/home/glassfish:/sbin/nologin

* Configure virutal servers/virtual hosts?

* Change folder where logs are stored
  http://docs.sun.com/app/docs/doc/821-1751/abluj?l=en&a=view

  stop glassfish
  vi /usr/local/glassfish/glassfish/domains/domain1/config/logging.properties
  change .sun.enterprise.server.logging.GFFileHandler.file

* Check if the log files are to big, backup, rotate.

* Kolla av olika profiler (develop/cluster/enterprise)

* Monitor software
  In the "has anything changed, tool" run this, and see if any
  values has been changed since last time the report was executed.

  * generate-jvm-report --type summary
  * It exist a monitor thing in the admin console.

  * Might be another command that makes the result easier to parase.
    asadmin> list-system-properties
    asadmin> list-applications --type web
    asadmin> list-containers
    asadmin> list-modules
    asadmin> list-commands --localonly
    asadmin> list-timers server
    asadmin> show-component-status MEjbApp
    asadmin> uptime
    asadmin> generate-jvm-report --type summary
    asadmin> list-logger-levels

 * Optimizations
   http://www.oracle.com/technetwork/java/javase/tech/vmoptions-jsp-140102.html

* Setup Thread pools
  http://docs.sun.com/app/docs/doc/821-1751/abluc?l=en&a=view
  asadmin> list-threadpools

* Something to read.
  http://kalali.me/learning-glassfish-v3-command-line-administration-interface-cli/

* Secure glassfish some more
  change /opt/glassfishv3/glassfish/domains/domain1/config/domain.xml
  Didn't get this to work. Need to use --secure on all asadmin.
  Maybe it works in glassfish 3.1
  The creates ssl connection between asadmin and DAS or other nodes
  TODO:general.shell_exec("/usr/local/glassfish/bin/asadmin set server-config.network-config.protocols.protocol.admin-listener.security-enabled=true", user="glassfish")

* Something in glassfish might need this, according to install requriments.
  yum install compat-libstdc++ compat-libgcc

* Extending and Updating GlassFish Server Inside a Closed Network
   http://docs.sun.com/app/docs/doc/821-1751/gjcya?l=en&a=view

* Log to syslog instead??
  com.sun.enterprise.server.logging.SyslogHandler.useSystemLogging=true
  Write to system log:
  Enabled
  Use UNIX syslog service to produce and manage log messages
  Log to Console:
  Enabled
  Write log messages to system console

* Turn on proxy
  Might be useful if the server is locked down, and need to reach internet.
  http://download.oracle.com/javase/6/docs/technotes/guides/net/proxies.html
  /usr/local/glassfish/bin/asadmin create-jvm-options -Dhttp.proxyHost=my.proxy.host
  /usr/local/glassfish/bin/asadmin create-jvm-options -Dhttp.proxyPort=3128

* Activate mod_jk and loadbalancing?
  Use mod_jk to loadbalance between tc and nsg servers, maybe between nodes
  in a cluster?
  administration-guide.pdf page 118

* Forward SSL cert from apache to glassfish.
  Documentation exists in redmine

* Read performance-tuning-guide.pdf

mysql
-----

* http://www.mysqlperformanceblog.com/2007/11/03/choosing-innodb_buffer_pool_size/
* Remove the root user, only have personal sysop accounts.
* defragment_all_tables():
*   ALTER TABLE xxx ENGINE=INNODB
* calculate_cardinality():
    Unlike MyISAM, InnoDB does not store an index cardinality value in its
    tables. Instead, InnoDB computes a cardinality for a table the first time
    it accesses it after startup. With a large number of tables, this might take
    significant time. It is the initial table open operation that is important,
    so to "warm up" a table for later use, access it immediately after startup
    by issuing a statement such as SELECT 1 FROM tbl_name LIMIT 1.
* Test mysql proxy - http://dev.mysql.com/doc/refman/5.1/en/mysql-proxy.html
* Test mysql heartbeat - http://dev.mysql.com/doc/refman/5.1/en/ha-heartbeat.html
* Backup innodb??
    http://www.learn-mysql-tutorial.com/BackupRestore.cfm
    http://www.innodb.com/doc/hot_backup/manual.html
    1 Shut down your MySQL server, ensure shut down proceeds without errors.
    2 Copy all your data files (ibdata files and .ibd files) into a secure and reliable location.
    3 Copy all your ib_logfile files.
    4 Copy your configuration file(s) (my.cnf or similar).
    5 Copy all the .frm files for your InnoDB tables.

    In addition to making binary backups, you should also regularly make dumps of
    your tables with mysqldump. The reason for this is that a binary file might be
    corrupted with no visible signs. Dumped tables are stored into text files that
    are simpler and human-readable, so spotting table corruption becomes easier.
    mysqldump also has a --single- transaction option that you can use to make a
    consistent snapshot without locking out other clients.

* Need a script to check if the innodb tablespace is about to be empty.
* Investigate --chroot=name
* monitor mysql, show inodb status;
* Is binary logs properly purged
    SHOW SLAVE STATUS
    PURGE BINARY LOGS BEFORE '2008-04-02 22:46:26';
* Modify table cache
    http://dev.mysql.com/doc/refman/5.0/en/server-system-variables.html#sysvar_table_cache
    show status like '%Opened_tables%';
    shows a lot of opened files, you might like to increase table cache
* Optimization
    http://dev.mysql.com/doc/refman/5.0/en/order-by-optimization.html
