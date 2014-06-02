#!/bin/sh

################################
#
# 01fo-dev-sys-backup.sh
#
# @changed: 2008-08-10
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################

DOW=`date +%u`

######################3
# SÂ slipper vi "Removing leading `/' from member names" p√•ar
cd /

###############
# Backup
service mysqld stop
tar czf /opt/fareoffice/AutomaticBackups/develop/fo-dev-sys/day-$DOW-fo-dev-sys.tar.gz var/lib/mysql
service mysqld start
