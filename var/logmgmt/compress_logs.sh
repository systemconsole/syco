#!/bin/sh
date=`date +%F`

base_path=/var/log/remote/
date_str=`date "+%Y/%m/" -d yesterday`

day=`date "+%d" -d yesterday`
cmd="tar -C $base_path$date_str -cvjf $base_path$date_str$day.tbz $day"

echo "Compressing log files in $base_path$date_str$day....."
#echo $cmd
$cmd
OUT=$?
if [ $OUT -ne 0 ]; then
	echo "Failed to compress log files"
	echo
else
	echo "Compressing success... removing files..."
	rm_cmd="rm -rf $base_path$date_str$day"
	echo $rm_cmd
	$rm_cmd
fi 
exit $OUT
