#!/bin/bash

#yum install -y sharutils

BOUNDARY="=== This is the boundary between parts of the message. ==="

SUBJECT="Client cert luaneu"
MAILFROM="sysop@fareoffice.com"
MAILTO="daniel@cybercow.se"
ZIPFILE="/home/luaneu/openvpn_client_keys.zip"
{
   echo  "From: $MAILFROM"
   echo  "To: $MAILTO"
   echo  "Subject:" $SUBJECT
   echo  "MIME-Version: 1.0"
   echo  "Content-Type: MULTIPART/MIXED; "
   echo  "    BOUNDARY="\"$BOUNDARY\"
   echo
   echo  "        This message is in MIME format.  But if you can see this,"
   echo  "        you aren't using a MIME aware mail program.  You shouldn't "
   echo  "        have too many problems because this message is entirely in"
   echo  "        ASCII and is designed to be somewhat readable with old "
   echo  "        mail software."
   echo
   echo  "--${BOUNDARY}"
   echo  "Content-Type: TEXT/PLAIN; charset=US-ASCII"
   echo
   echo  "This email comes with multiple attachments."
   echo
   echo
   echo  "--${BOUNDARY}"
   echo  "Content-Type: application/zip; charset=US-ASCII; name="${ZIPFILE}
   echo  "Content-Disposition: attachment;   filename="`basename ${ZIPFILE}`
   echo
   uuencode $ZIPFILE $ZIPFILE
   echo
   echo  "--${BOUNDARY}--"
} | /usr/lib/sendmail -t
