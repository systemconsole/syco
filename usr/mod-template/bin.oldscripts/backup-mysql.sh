#!/bin/sh
#mysqldump --all-databases > /var/backup/mysql-$(date +%Y-%m-%d-%H.%M.%S).sql
FILENAME="/var/backup/mysql-$(date +%u-%A).sql.gz"
echo "Dump to $FILENAME"
mysqldump --all-databases > $FILENAME