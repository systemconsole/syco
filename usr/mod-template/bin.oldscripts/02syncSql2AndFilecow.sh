#!/bin/sh

################################
# Backup script for filecow
#
# * Download backups from mail.fareoffice.com
# * Download backups from devcow
# * Download mysql backup from sql2.fareoffice.com
# * Copy backups from filecow to sql2.fareoffice.com
#
# @author Daniel Lindh <daniel@fareoffice.com>
# @package Backup
################################

# DayOfWeek
#DOW=`date +%u%a`

DOW=`date +%u`

######################3
# S� slipper vi "Removing leading `/' from member names" p� tar
cd /

################################
# Download backups from remote servers
#
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/day-$DOW-fo-dp-sql2.tar.gz /opt/backup/AutomaticBackups/production/fo-dp-sql2
logger backup hämtat från sql2 ok
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa backup@dpwww2.fareoffice.com:/opt/fareoffice/AutomaticBackups/production/fo-dp-www2/day-$DOW-fo-dp-www2.tar.gz /opt/backup/AutomaticBackups/production/fo-dp-www2
logger backup hämtat från www2 ok





#fo-dev-php
/usr/bin/scp -C -i /home/backup/.ssh/id_dsa backup@fo-dev-php.fareonline.net:/opt/fareoffice/AutomaticBackups/develop/fo-dev-php/day-$DOW-fo-dev-php.tar.gz /opt/backup/AutomaticBackups/develop/fo-dev-php
logger backup hämtat från fo-devphp ok

#fo-dev-svn
/usr/bin/scp -C -i /home/backup/.ssh/id_dsa backup@fo-dev-svn.fareonline.net:/opt/fareoffice/AutomaticBackups/develop/fo-dev-svn/day-$DOW-fo-dev-svn.tar.gz /opt/backup/AutomaticBackups/develop/fo-dev-svn
logger backup hämtat från fo-dev-svn ok

#fo-dev-sys
/usr/bin/scp -C -i /home/backup/.ssh/id_dsa backup@fo-dev-sys.fareonline.net:/opt/fareoffice/AutomaticBackups/develop/fo-dev-sys/day-$DOW-fo-dev-sys.tar.gz /opt/backup/AutomaticBackups/develop/fo-dev-sys 
logger backup hämtat från fo-dev-sys ok

#fo-dev-wiki
/usr/bin/scp -C -i /home/backup/.ssh/id_dsa backup@fo-dev-wiki.fareonline.net:/opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki/day-$DOW-fo-dev-wiki.tar.gz /opt/backup/AutomaticBackups/develop/fo-dev-wiki
logger backup hämtat från fo-dev-wiki ok


##################################
# Utvecklingsmiljo 
# Matte ligger i egen fil nu
#
#rsync -avz -e ssh root@192.168.3.21:/opt/fareoffice/mysql/ 
#/opt/backup/AutomaticBackups/develop/fo-dev-mysql/
#logger backup hämtat från fo-dev-mysql ok

#rsync -avz -e ssh root@192.168.3.20:/home/glassfish/    
#/opt/backup/AutomaticBackups/develop/fo-dev-glassfish/
#logger backup hämtat från fo-dev-glassfish ok

#rsync -avz -e ssh root@192.168.3.11:/opt/fareoffice/mysql/ 
#/opt/backup/AutomaticBackups/develop/fp-dev-mysql/
#logger backup hämtat från fp-dev-mysql

#rsync -avz -e ssh root@192.168.3.10:/home/glassfish/    
#/opt/backup/AutomaticBackups/develop/fp-dev-glassfish/
#logger backup hämtat från fp-dev-glassfish

########################
# Mailen lite senare
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa backup@fo-dev-mail.fareonline.net:/opt/fareoffice/AutomaticBackups/develop/fo-dev-mail/day-$DOW-fo-dev-mail.tar.gz /opt/backup/AutomaticBackups/develop/fo-dev-mail/
logger backup hämtat från fo-dev-mail ok

################################
# Upload backups to sql2.fareoffice.com"
#
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Home.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-file
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Document.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-file
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-mail/day-$DOW-fo-dev-mail.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-mail
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-php/day-$DOW-fo-dev-php.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-php
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-svn/day-$DOW-fo-dev-svn.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-svn
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-sys/day-$DOW-fo-dev-sys.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-sys
/usr/bin/scp -C -i /home/backup/.ssh/idsql2/id_dsa /opt/backup/AutomaticBackups/develop/fo-dev-wiki/day-$DOW-fo-dev-wiki.tar.gz backup@dpsql2.fareoffice.com:/opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki


logger backup filekopiering på sql och filecow har gjorts helt klar
