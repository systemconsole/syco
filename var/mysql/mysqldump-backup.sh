#!/bin/sh
#
# mysqldump-backup.py
#
# Does a mysqldump backup of alla mysql databases on the current server.
#
# REQUIREMENTS
# ============
#
# This file needs to be created, to do it possible for the mysql client to
# login to the mysql database without exposeing the mysql password on command
# line (ps aux) or in this script.
#
# /root/.my.cnf
# [client]
# user=root
# password="<password>"
#
# __author__ = "daniel.lindh@cybercow.se"
# __copyright__ = "Copyright 2011, The System Console project"
# __maintainer__ = "Daniel Lindh"
# __email__ = "syco@cybercow.se"
# __credits__ = ["???"]
# __license__ = "???"
# __version__ = "1.0.0"
# __status__ = "Production"


mkdir -p /var/backup/
FILENAME="/var/backup/mysql-$(date +%u-%A).sql"
echo "Dump to $FILENAME"
mysqldump --all-databases --lock-all-tables > $FILENAME
gzip -f $FILENAME
