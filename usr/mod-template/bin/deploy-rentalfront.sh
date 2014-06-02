#!/bin/sh

su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 list-applications"

su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 undeploy rentalfront-xml-client-1.0.1"
su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 undeploy rentalfront-backstage-0.8.0"
su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 undeploy rentalfront-ecl-0.8.0"

/etc/init.d/glassfish-3.1.1 restart

rm -rf /tmp/release
mkdir -p /tmp/release
cd /tmp/release

wget --user=syscon --password="PASSWORD" http://www.fareonline.net/fo/tags/rentalfront/ecl/0.8.0-SNAPSHOT/dist/rentalfront-ecl-0.8.0.ear
wget --user=syscon --password="PASSWORD"  http://www.fareonline.net/fo/tags/rentalfront/ecl/0.8.0-SNAPSHOT/dist/rentalfront-xml-client-1.0.1.war
wget --user=syscon --password="PASSWORD"  http://www.fareonline.net/fo/tags/rentalfront/backstage/main/0.8.0-SNAPSHOT/dist/rentalfront-backstage-0.8.0.ear

su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 deploy rentalfront-ecl-0.8.0.ear"
su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 deploy rentalfront-backstage-0.8.0.ear"
su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 deploy --contextroot=rentalfront-xml-client rentalfront-xml-client-1.0.1.war"

su glassfish -c "/usr/local/glassfish-3.1.1/bin/asadmin --port 6048 list-applications"
