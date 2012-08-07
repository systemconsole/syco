#!/bin/sh
#
# svndump-backup.sh
#
# Does a svn dump backup of all svn databases on the current server.
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

for f in `ls /svn`
do
    FILENAME="/var/backup/svn-$f-$(date +%u-%A).dump"
    echo "Dump to $FILENAME"
    svnadmin dump /svn/$f > $FILENAME ;
    gzip -f $FILENAME
done
