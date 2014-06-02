#!/bin/bash	
# small script the collects evidence files from hosts to audit for PCI DSS


function usage () 
{
	echo "`basename $0` <iplist file>|-host <host>"
	exit
}

if [[ $1 == "" ]]; then usage; fi
hostfile=$1

if [[ $1 =~ ^-host ]]; then
	tmpfile=`mktemp`
	hostfile=$tmpfile
	if [ "$2" == "" ]; then usage; fi
	echo $2 > $hostfile
fi

ssh="ssh -t -q"

if [ ! -d auditPCI ]; then echo "folder auditPCI not found." ; exit; fi

echo -n "Please enter your remote sudo password: "
read -s sudopass

for ip in `cat $hostfile | egrep -v "^#"`; do
	echo "-----------------------------------------------------------------"
	echo "Server: $ip"
	echo "-----------------------------------------------------------------"
	
	echo "syncing folder auditPCI to the target machine.."
	rsync -avrq auditPCI $ip:/tmp

	echo "running the audit.."
	$ssh $ip "echo $sudopass | sudo -S python /tmp/auditPCI/__init__.py"

	echo "chmodding the results.."
	$ssh $ip "echo $sudopass | sudo -S chmod o+x /tmp/syco/"
	$ssh $ip "echo $sudopass | sudo -S chmod -R o+r /tmp/syco/"

	echo "syncing back the results.."
	rsync -avrq $ip:/tmp/syco/static/* $HOME/syco-logs/html

	echo "-----------------------------------------------------------------"
	echo "End output for $ip"
	echo "-----------------------------------------------------------------"
	echo
done

if [ -r $tmpfile ]; then rm -f $tmpfile; fi
