#!/bin/sh

################################
#
# 01fo-dev-php-backup.sh
#
# Ska ligga på sql2.fareoffice.com:/opt/fareoffice/ShScript
#
# @changed: 2008-08-10
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################

DOW=`date +%u`

####################
# Skapa kataloger.
echo "Create directories"
mkdir -p /opt/fareoffice/ShScript
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-file
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-mail
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-php
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-svn
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-sys
mkdir -p /opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki
mkdir -p /opt/fareoffice/AutomaticBackups/production/fo-dp-www2/
mkdir -p /opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/

######################################
# Backup
sudo mysql.sh stop
cd /
tar zcvf /opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/day-$DOW-fo-dp-sql2.tar.gz usr/local/mysql/data/* usr/lib/FoLanguage.so usr/lib/FoFunctions.so etc/my.cnf

sudo mysql.sh start

