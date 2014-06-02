#!/bin/sh
sudo rpm -Uhv http://download.fedora.redhat.com/pub/epel/6/x86_64/epel-release-6-5.noarch.rpm
yum -y install git
cd /opt
git clone https://github.com/systemconsole/syco.git
mkdir -p /opt/syco/usr
cd /opt/syco/usr
git clone git@10.100.100.11:/git/syco-private.git
cd /opt/syco/usr/syco-private/etc
ln -s install-tc.cfg install.cfg
cd /opt/syco/bin
./syco.py install-syco
./syco.py install-local
