* Jag misstänker att backupen inte funkar för nya miljön. Bör verifireras.
* Alla none www domains måste gås igenom och pekas om till rätt ip. alamo.co.uk pekar mot IBT.
* Rsyslog.conf och kanske httpd.confar har troligen inte alla interna ip-nummber för Availo. Åtminstone rsyslog.conf saknade det. (webres)
* Synca alla installFirewall script och conf filer. Checka in till syco-private
* Skapa icinga-test för att kontrollera att backup:er görs.
* Installera WebRes selenium test på alla Sysop:ars datorer så att dessa kan köras före/efter hallbyte på både passiv och aktiv hall
* Uppdatera syco install script så att sendmail antingen inte finns (php skickar via postfix) eller att sendmail konfigureras ordentligt. (Daniel kommentar: Detta är ett problem jag tror vi bara har på Centos 5.x, alltså webres servern)
* Undersök möjligheter att övervaka och notifiera när vi slår i bandbreddstaket
* Undersök möjligheter att övervaka och notifiera när vi har mer mod_sec blocks än vanligt
* Undersök möjligheter att övervaka våra att mailutskick fungerar (PTR) etc.
* Flytta alla nagios test ifrån kontoret till ICINGA.


* Detta är gjort på både webres-tc och av. Måste in i syco, eller någon howto.
# MEM

setmaxmem webres-tc --kilobytes 20971520
setmem webres-tc --size 20971520

# CPU
edit webres-tc

    <vcpu placement='static'>16</vcpu>

setvcpus webres-tc --count 16
vcpuinfo webres-tc
vcpupin webres-tc 0 0-15  --config --live
vcpupin webres-tc 1 0-15  --config --live
vcpupin webres-tc 2 0-15  --config --live
vcpupin webres-tc 3 0-15  --config --live
vcpupin webres-tc 4 0-15  --config --live
vcpupin webres-tc 5 0-15  --config --live
vcpupin webres-tc 6 0-15  --config --live
vcpupin webres-tc 7 0-15  --config --live
vcpupin webres-tc 8 0-15  --config --live
vcpupin webres-tc 9 0-15  --config --live
vcpupin webres-tc 10 0-15 --config --live
vcpupin webres-tc 11 0-15 --config --live
vcpupin webres-tc 12 0-15 --config --live
vcpupin webres-tc 13 0-15 --config --live
vcpupin webres-tc 14 0-15 --config --live
vcpupin webres-tc 15 0-15 --config --live
vcpupin webres-tc

* Funkar backupen?


WebRes installera  mkdir -p /opt/RootLive/Site/DistEnterpriseProduction/Temp/Cache/smarty/templates_c

-------------------------------------------------------------------------------
- Step 3
-------------------------------------------------------------------------------
* Reinstall all servers at office.

Shutdown Tonys servers
-------------------------------
* Ask Tony to move the integration stuff to the new servers.
* Keep anything else from Tonys FP servers?
* Shutdown Tonys old FP servers.
* Install hudson/sonar and other tools on Tonys servers?

* Rename all webres github repos.
-------------------------------------------------------------------------------
- Step 4
-------------------------------------------------------------------------------

EHI
---

* IPV6 in China?
* Start IPV6 project for Swedish Data Centers.
  Can we use iptables to masqurade both external ipv4 and ipv6 to internal
  ipv4?
* Generate a monthly report including
  * Uptime
  * Response time
  * Incidents
  * Support hours
  * Look and Books
  * Hits on the server
  * Amount of data sent/recv to server.
  * Add other data from munin and nagios.


-------------------------------------------------------------------------------
- Step 5
-------------------------------------------------------------------------------

* CLAM
  How many times per hour shall I run freshclam?
  You can check for database update as often as 4 times per hour provided that you have the following options in freshclam.conf: DNSDatabaseInfo current.cvd.clamav.net DatabaseMirror db.XY.clamav.net DatabaseMirror database.clamav.net Replace XY with your country code. If you don’t have that option, then you must stick with 1 check per hour.

* installFarepayment - Borde nästan fixa så att installationen utav FP uat sparar nytt surfcert i ecl test keystoren automatiskt i install scriptet

* switchDataCenter script

* Clam installation through RPM, or create our own RPM.
  http://solutionsfox.com/2011/04/install-clamav-on-redhat-or-centos/
* Remove authorized_keys on all servers.
  syco clean-up???
* syco password-generate (randomize all passwords with general.generate_pas..)
* Better crypt of the passwordstore.
* Look if alienvault uses tools we are not using. Something to install by us?
* Check that everybody has changed their ldap password, so nobody uses fe...?
* FYI så behövde jag idag ssh access för att se vilken tag som senast releasats till prod. Vore bra om det kunde läggas in som en feature i sycochuck ;)

More iptables
----------------------

* http://gr8idea.info/os/tutorials/security/iptables5.html

* Separate rules for eth0 and eth1, br0 and br1?

* Iptables should only allow port 80 to official yum repo servers, for all
  other servers it should be blocked. Don't disable the code handling
  httpd installation.

* Create the allowed_tcp/udp directly under INPUT to first filter on tcp or udp.
  The same with OUTPUT and FORWARDING. This will optimize all rules by "50%".

* Don't try to delete chains, when they don't exist. To remove the error message from iptables.

* Are all tftp rules properly configured?
  http://lonesysadmin.net/2007/10/29/how-to-install-a-tftp-server-on-red-hat-enterprise-linux/
  # /etc/sysconfig/iptables-config
  # Add IPTABLES_MODULES="ip_conntrack_tftp"

* Setup a blacklist of ips that will be blocked for a given amount of time.
  Possible to add ips on the fly when certain actions are done, for example
  when someone port scans our server. We also need to white list some servers
  like our own security scanners. Maybe using ipt_recent.
  Even better if we could also share the black list between servers.

  http://www.snowman.net/projects/ipt_recent/
  http://www.frozentux.net/iptables-tutorial/scripts/recent-match.txt

* Use ipchains, to limit speed and other for bots etc.
  http://linux-ip.net/articles/Traffic-Control-HOWTO/elements.html#e-shaping


Harden/Refactoring of webres installation
-----------------------------------------

* Install WebRes should install vsftp and users.

* Migrate with old chuck and mattes bootstrap-chuck
* Move functions from fareoffice-sysop to sycochuck

* Instead of using part of folder name (enterprise-tech) as environment use
  enterprise-tech/etc/fareoffice.ini variable

* Script to generate host file, update README.

* Enable ; http://www.php.net/manual/en/outcontrol.configuration.php#ini.output-buffering

* In php.ini remove E_NOTICE, and log files will be full of stuff.
  error_reporting  =  E_ALL & ~E_NOTICE & ~E_DEPRECATED

* Move some of the scripts in fareoffice/bin to syco-swiss
  A separate project with utility script that are not dependent on any
  include files.

* Move more code from syco installFareoffice to fareoffice/bin/setup-*

* Document network layout and functionality of all office and prod servers
  in red mine.

* jaila apache på qa, för att att det fungerar 
  http://www.cyberciti.biz/tips/chroot-apache-under-rhel-fedora-centos-linux.html 
  http://www.faqs.org/docs/securing/chap29sec254.html
* Disabla exec i php
* Byta pdf genereringen
* Byta ut exec('iconv
* Spärra utgående trafik på port 80 (inte mot localhost)
* Spärra mer portar.
* täppa till alla include sudo
  find . -type d \( -name Dynamic -o -name Temp -o -name static[.] \) -prune -o -exec grep -H "include\(_once\)([^'\"]" {} \;
* ej tillåtta externa includes allow_url_fopen = O
 http://php.net/manual/en/filesystem.configuration.php
* Säkra servern mera
   * http://httpd.apache.org/docs/2.0/misc/security_tips.html 
  * http://www.owasp.org/index.php/PHP_Top_5
* selinux
  h ttp://beginlinux.com/server_training/web-server/976-apache-and-selinux
* php_safe_mode
* mod-security.


-------------------------------------------------------------------------------
- NOT PRIOROTIZED
-------------------------------------------------------------------------------

* Add proper licence to all files. Add licence file to root folder.

* Do something with this info??
  # failed atempts
  /usr/bin/last -f /var/log/btmp
  # Last logins
  /usr/bin/last


Hardening
---------

* 16h - Setup  /etc/hosts.allow and ate /etc/hosts.deny  from iptables script.
  # echo "ALL: ALL" >> /etc/hosts.deny
* 8h - Secure SSH?
  http://serverfault.com/questions/334448/why-is-ssh-password-authentication-a-security-risk?newsletter=1&nlcode=30229%7c0cb7
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
* Apply
  CIS 6.3.4 Set Lockout for Failed Password Attempts (Not Scored)
  CIS 6.3.5 Use pam_deny.so to Deny Services (Not Scored)


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
* Run cobbler unconfined?
  https://github.com/cobbler/cobbler/wiki/Selinux
* Check this, something we should/can use?
  fencing tools were not found, and are required to use the (optional) power management features. install cman or fence-agents to use them

KVM
---

* KVM - Experiment with vcpus, and dedicate them to real cores.
  Maybe
  1-4   - Shared between some utility servers.
  5-16  - Webres-av
  17-20 - Shared between some utility servers.
  21-32 - Mysql1-av
* Add --cpuset=auto thingy to cobbler installed guests, to get the right NUMA.
* Setup console
  http://www.cyberciti.biz/faq/linux-kvm-redirecting-freebsd-virtual-machines-console-to-aserialport/
* http://www.linux-kvm.org/page/Tuning_KVM
* http://www.linux-kvm.org/page/Tuning_Kernel
* http://www.linux-kvm.org/page/HOWTO
* Try --extra-args "console=ttyS0,115200 text headless"
  on virt-install.
  http://serverfault.com/questions/257962/kvm-guest-installed-from-console-but-how-to-get-to-the-guests-console


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

* Should Production and Telefonplan use different domain.ldif files
  * Should all office servers use the production ldap server.
  * Should we connect glassfish to ldap.
  * Look into samba 4 and FreeIpa/389.

* Radius shouldn't use the manager account to access ldap
  /etc/raddb/modules/ldap
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
  https://github.com/Yubico/yubico-pam/wiki/YubiKeyAndOpenVPNviaPAM
* 2-factor auth
  http://www.wikidsystems.com/
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
* Store hosts in ldap?
* Backup the LDAP database. Primary the passwords need backup.
* Install secondary "read-only" ldap server.
* Read for more features
  http://www.openldap.org/doc/admin24/OpenLDAP-Admin-Guide.pdf
* nfs mount fo-tp-file?
* vpn create sync with ldap users.

Load balancing
--------------
* Investigate DNS and load balancing
  http://www.zeus.com/products/global-load-balancer
  F5 GTM
  Ultra dns
  Lokal loadbalancing http://www.ultramonkey.org/3/
* Investigate bgp ip anycast.

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

  * Might be another command that makes the result easier to parse.
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

* Check if possible to install zlib in mysql (compile it into it.)

* syco should install this automatically.
  see /opt/syco/var/mysql/mysql-lvm-backup.sh

* Update binlog purger on fo-nsg-db1.
  Should check the sync on the slave servers, and then delete binlogs on the master server that has been replicated.
* A script checking mysql.err for new entries.
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

