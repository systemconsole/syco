#!/bin/sh

################################
#
# mysql-rsnapshot-backup.sh
#
# l
# http://poller.se/2010/12/rsnapshot-and-mysqldump/
# http://rsnapshot.org/rsnapshot.html
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################

#/root/.my.cnf
# command line arguments are visible to other users.
[client]
user=root
password=<password>

# Rsnapshot
backup_script   /usr/bin/ssh root@example.com "/root/mysql-rsnapshot-backup.sh run"   unused0/
backup          root@example.com:/tmp/mysqldump/                      				  example.com/
backup_script   /usr/bin/ssh root@example.com "/root/mysql-rsnapshot-backup.sh clean" unused1/

# Script
#!/bin/bash
 
PATH="/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin"
 
backupdir="/var/mysqldump"
 
chmod -R 700 $backupdir
 
case $1 in
	run)
    	for db in `mysql --defaults-file=.my.cnf -e 'show databases' |tr -d '| ' |grep -v 'Database' |grep -v 'information_schema'`; do
        	mysqldump --defaults-file=.my.cnf $db | gzip > $backupdir/$db.sql.gz
        done
	;;
 
    clean)
    	rm -f $backupdir/*.sql.gz
	;;
esac