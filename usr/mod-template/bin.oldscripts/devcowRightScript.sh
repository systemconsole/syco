#!/bin/sh

#
# devcowRightScript.sh
#
# Sätter rättigheter på devcow
# 

echo "------------ FILES --------------"
cd /opt/disk1/docs
chown -R root:public .

# www behöver execute rättigheter.
chmod 774 .

find * -type d -exec chmod 770 {} \;
find * -type f -exec chmod 660 {} \;

echo "------------ DOCUMENT ------------"
cd /opt/disk1/docs/Document
chown -R root:board 4\ Board/

echo " ------------ TIDREDOVISNINGSRÄTTIGHETER ------------"
cd /opt/disk1/docs/Document/6\ Tidredovisning

chown martin:board        101\ Martin\ Palmer\ 2005.xls
chown daniel:board        102\ Daniel\ Lindh\ 2005.xls
chown nordlander:board    103\ Per\ Norlander\ 2005.xls
chown frederik:board      118\ Frederik\ Stade\ 2005.xls
chown hellman:board       122\ Mikael\ Hellman\ 2005.xls
chown root:board 2004/
chown root:board 2005FramTillMaj/
chown root:board Mallar/

echo "------------ DEVCOW ------------"
cd /opt/RootLive
chown -R www:public .

echo "------------ HOME KATALOGER ------------"
cd /home
find . -type d -exec chmod 700 {} \;
find . -type f -exec chmod 600 {} \;

chown -R martin:root     martin                     
chown -R hellman:root    hellman                  
chown -R daniel:root     daniel                     
chown -R frederik:root   frederik                  
chown -R hwimer:root     hwimer                     
chown -R pernilla:root   pernilla                  
chown -R roger:root      roger                     

echo "------------ SHSCRIPT ------------"
cd /opt/disk1/docs/ShScript
chown -R root:public .
chmod -R 740 *
