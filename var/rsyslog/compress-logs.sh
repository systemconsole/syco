#!/bin/bash

# __author__ = "daniel@cybercow.se, anders@televerket.net"
# __copyright__ = "Copyright 2012, The System Console project"
# __maintainer__ = "Daniel Lindh"
# __email__ = "syco@cybercow.se"
# __credits__ = ["???"]
# __license__ = "???"
# __version__ = "1.0.0"
# __status__ = "Production"

# Where the ryslogd remote files are stored.
base_path=/var/log/rsyslog/

#
# Compress and remove a folder.
#
#
compress_folder() {
    # Does it exist any log files for yesterday.
    base_path=$1
    date_str=$2
    day=$3
    if [ -d "$base_path$date_str$day" ]; then
        cmd="tar -C $base_path$date_str -cvjf $base_path$date_str$day.tbz $day"

        echo "Compressing log files in $base_path$date_str$day."
        echo $cmd
        $cmd
        OUT=$?
        if [ $OUT -ne 0 ]; then
            txt="[ERROR] Failed to compress rsyslgd log files."
        	echo txt
        	echo
            logger -t syco -p user.crit txt
        else
            txt="[NOTICE] Compression of rsyslgd $base_path$date_str$day succeded."
        	echo $txt
            logger -t syco $txt

            #
            txt="[NOTICE] Removing folder $base_path$date_str$day."
            echo $txt
            logger -t syco $txt

        	rm_cmd="rm -rf $base_path$date_str$day"
        	$rm_cmd
        fi
    fi
}

echo "Compress rsyslogd $base_path"

# Compress the last 30 days folders. Should only be last day.
# But if the compression for some reason gets halted, this will fix it.
for((i=1; i <=30 ; i++))
do
    # Part of path to the month of last day. ie 2012/11
    date_str=`date "+%Y/%m/" -d "-$i day"`

    # Part of path to yesterday, ie 08
    day=`date "+%d" -d "-$i day"`
    compress_folder $base_path $date_str $day
done
