#!/bin/sh

################################
#
# 01fo-dp-www2-backup.sh
#
# @changed: 2008-08-10
#
# @author Daniel Lindh <daniel@fareoffice.com>
################################

DOW=`date +%u`

######################3
# Så slipper vi "Removing leading `/' from member names" på tar
cd /

###############
# Backup
cd /
tar czf /opt/fareoffice/AutomaticBackups/production/fo-dp-www2/day-$DOW-fo-dp-www2.tar.gz \
        --exclude CacheFiles \
        --exclude NoBackup \
        usr/local/sbin \
        usr/lib/libngapi.so \
        etc \
        opt/RootLive
