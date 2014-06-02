#!/bin/sh

################################
# Restore the lst backup of the mysql db on sql2.fareoffice.com 
# to devcow (foMasterLive)
#
#
# @author Daniel Lindh <daniel@fareoffice.com>
# @package Backup
################################

# Year Mont Day
YMD=`date +%Y-%m-%d`

# DayOfWeek
DOW=`date +%u%a`

# Tar bort gamla databasen.
/usr/local/bin/mysql.server stop

mkdir /usr/local/mysql/var/foMasterLive
rm /usr/local/mysql/var/foMasterLive/*

mkdir /usr/local/mysql/var/foVanguardUnicodeLive
rm /usr/local/mysql/var/foVanguardUnicodeLive/*

/usr/local/bin/mysql.server start


# Packar upp nya databasen.
mkdir /home/daniel/NoBackup/mysql/
cd /home/daniel/NoBackup/mysql/
tar zxf /opt/disk1/docs/Backup/AutomaticBackups/sql/LastWeek-$DOW-MysqlAllFilesBackup.tar.gz 

mv /home/daniel/NoBackup/mysql/usr/local/mysql/data/foMaster/* /usr/local/mysql/var/foMasterLive/
mv /home/daniel/NoBackup/mysql/usr/local/mysql/data/foVanguardUnicode/* /usr/local/mysql/var/foVanguardUnicodeLive/

rm -r /home/daniel/NoBackup/mysql
chmod 777 /usr/local/mysql/var/foMasterLive/*
chmod 777 /usr/local/mysql/var/foVanguardUnicodeLive/*

/usr/local/bin/mysql.server restart


