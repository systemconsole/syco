#!/bin/sh

CMD="DELETE FROM SystemEvents WHERE ReceivedAt < DATE_SUB(NOW(),INTERVAL $1 DAY);"
echo ""
echo $CMD
/usr/bin/env mysql -u${mysql_user} -p${mysql_password} syslog -e"$CMD"
OUT=$?
if [ $OUT -ne 0 ]; then
	echo "Failed to remove data"
	echo
else
	echo "Removed data from sql"
fi 
exit $OUT

