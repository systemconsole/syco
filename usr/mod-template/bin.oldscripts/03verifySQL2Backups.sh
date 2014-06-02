#!/bin/sh

################################
#
# 03verifySQL2Backups.sh
#
# * Verify backups
# * Make montly backups
#
# @changed: 2008-08-10
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################

# Year Mont Day
YMD=`date +%Y-%m-%d`

# DayOfWeek
DOW=`date +%u`

################################
# Verify backups...

FILELIST=\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Document.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Home.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-mail/day-$DOW-fo-dev-mail.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-php/day-$DOW-fo-dev-php.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-svn/day-$DOW-fo-dev-svn.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-sys/day-$DOW-fo-dev-sys.tar.gz"\
"/opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki/day-$DOW-fo-dev-wiki.tar.gz"\
"/opt/fareoffice/AutomaticBackups/production/fo-dp-www2/day-$DOW-fo-dp-www2.tar.gz"\
"/opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/day-$DOW-fo-dp-sql2.tar.gz"

echo "Verify backups"
for filename in $FILELIST
do
	echo "   verify $filename"
  if ! tar ztf $filename > /dev/null 2>&1
  then
  	echo "      WARNING: File $filename on `hostname` is corrupt!"
    echo "This happend: `date`" | mail -s "File $filename on `hostname` is corrupt" failed_backup@fareonline.net -b sysop@fareoffice.com
	logger backuperror  WARNING: File $filename on `hostname` is corrupt!  
fi
done

################################
# WEEKLY Backups.
if [ "$DOW" = "1" ];
then
  echo "Create weekly backup"
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Document.tar.gz /opt/fareoffice/AutomaticBackups/develop/fo-dev-file/weekly-$YMD-fo-dev-file-Document.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-file/day-$DOW-fo-dev-file-Home.tar.gz     /opt/fareoffice/AutomaticBackups/develop/fo-dev-file/weekly-$YMD-fo-dev-file-Home.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-mail/day-$DOW-fo-dev-mail.tar.gz          /opt/fareoffice/AutomaticBackups/develop/fo-dev-mail/weekly-$YMD-fo-dev-mail.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-php/day-$DOW-fo-dev-php.tar.gz            /opt/fareoffice/AutomaticBackups/develop/fo-dev-php/weekly-$YMD-fo-dev-php.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-svn/day-$DOW-fo-dev-svn.tar.gz            /opt/fareoffice/AutomaticBackups/develop/fo-dev-svn/weekly-$YMD-fo-dev-svn.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-sys/day-$DOW-fo-dev-sys.tar.gz            /opt/fareoffice/AutomaticBackups/develop/fo-dev-sys/weekly-$YMD-fo-dev-sys.tar.gz
  cp /opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki/day-$DOW-fo-dev-wiki.tar.gz          /opt/fareoffice/AutomaticBackups/develop/fo-dev-wiki/weekly-$YMD-fo-dev-wiki.tar.gz
  cp /opt/fareoffice/AutomaticBackups/production/fo-dp-www2/day-$DOW-fo-dp-www2.tar.gz         /opt/fareoffice/AutomaticBackups/production/fo-dp-www2/weekly-$YMD-fo-dp-www2.tar.gz
  cp /opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/day-$DOW-fo-dp-sql2.tar.gz         /opt/fareoffice/AutomaticBackups/production/fo-dp-sql2/weekly-$YMD-fo-dp-sql2.tar.gz
fi

echo "done"
logger fo-dev-file backup vecko backupp gjort 
