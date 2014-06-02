##!/bin/sh
#############################
#
# 02syncWwwAndSql2.sh
#
# @changed: 2008-08-10
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################




#
#
DOW=`date +%u`


################################
# WWW.FAREOFFICE.COM - Get files from dpwww2.fareoffice.com
scp -C -i /home/backup/.ssh/idsql2/id_dsa backup@dpwww2.fareoffice.com:/opt/fareoffice/AutomaticBackups/production/fo-dp-www2/day-$DOW-fo-dp-www2.tar.gz /opt/backup/AutomaticBackups/production/fo-dp-www2


