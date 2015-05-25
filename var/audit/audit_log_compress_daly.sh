#!/bin/bash
FILE=/var/log/audit/audit.log.1
NOW=$(date +"%m_%d_%Y")

if [ -f $FILE ];
then
   echo "File $FILE exists."
   echo "Compressing"
   tar czf /var/log/audit_packed_$NOW.tar.gz /var/log/audit/audit.log.* --remove-files                          
else
   echo "File $FILE does not exist."
fi
