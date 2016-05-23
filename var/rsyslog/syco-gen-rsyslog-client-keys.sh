#!/bin/bash
if [ $# -eq 0 ]
  then
    echo "ERROR, Please specify a FQDN as argument to this script"
    exit 1
fi

mkdir /opt/syco/installtemp
chmod 777 /opt/syco/installtemp/
cp -f /etc/pki/rsyslog/template.server /opt/syco/installtemp/template.$1
sed -i "s/GEN-CN/$1/g" /opt/syco/installtemp/template.$1
sed -i "s/GEN-DNS-NAME/$1/g" /opt/syco/installtemp/template.$1
sed -i "s/GEN-SERIAL/$(date +%s)/g" /opt/syco/installtemp/template.$1
certtool --generate-privkey --outfile /etc/pki/rsyslog/$1.key
certtool --generate-request --load-privkey /etc/pki/rsyslog/$1.key --outfile /etc/pki/rsyslog/$1.csr --template /opt/syco/installtemp/template.$1
certtool --generate-certificate --load-request /etc/pki/rsyslog/$1.csr --outfile /etc/pki/rsyslog/$1.crt --load-ca-certificate /etc/pki/rsyslog/ca.crt --load-ca-privkey /etc/pki/rsyslog/ca.key --template /opt/syco/installtemp/template.$1
rm -rf /opt/syco/installtemp/
rm -f /etc/pki/rsyslog/$1.csr
rm -f /etc/pki/rsyslog/$1
echo
echo "Its done, the new files are"
ls -l /etc/pki/rsyslog/$1*
exit 0