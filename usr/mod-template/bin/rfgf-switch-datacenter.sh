#!/bin/sh

exit

Setup the temporary SSH-tunnel between rentalfront servers and fareoffice statistic db.




#
# Prepare database
#
delete from mysql.user where user like "ecls_%";
delete from mysql.db where user like "ecls_%";
GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE ON foStatisticProduction.* TO 'ecls_prod'@'10.100.22.11' IDENTIFIED BY 'b..';
GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE ON foStatisticProduction.* TO 'ecls_prod'@'10.100.12.11' IDENTIFIED BY 'b..';
GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE ON foStatisticRelease.* TO 'ecls_uat'@'10.100.22.11' IDENTIFIED BY 't..';
GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE ON foStatisticRelease.* TO 'ecls_uat'@'10.100.12.11' IDENTIFIED BY 't..';

flush privileges;
select user, host from mysql.user;

#
# Setup ssh tunnel
#
ssh-keygen
ssh-copy-id -i /root/.ssh/id_rsa.pub dali@db1-nsg.fareoffice.com
ssh-copy-id -i /root/.ssh/id_rsa.pub dali@db1-tc.fareoffice.com

yum install -y autossh
autossh -M 20000 -L 8006:10.100.22.11:3306 dali@db1-tc.fareoffice.com -Nf
vi /etc/rc.local

#
# Setup glassfish connecition pools
#
su glassfish
/usr/local/glassfish-3.1.1/bin/asadmin --port 6048
delete-jdbc-connection-pool  --cascade mysql_ecls
delete-password-alias mysql_ecls

create-password-alias mysql_ecls

#create-jdbc-connection-pool --datasourceclassname com.mysql.jdbc.jdbc2.optional.MysqlConnectionPoolDataSource --restype javax.sql.ConnectionPoolDataSource --property "serverName=localhost:port=8006:User=ecls_prod:Password=\$\{ALIAS\=mysql_ecls\}:characterEncoding=UTF-8:databaseName=foStatisticRelease" mysql_ecls

create-jdbc-connection-pool --datasourceclassname com.mysql.jdbc.jdbc2.optional.MysqlConnectionPoolDataSource --restype javax.sql.ConnectionPoolDataSource --property "serverName=localhost:port=8006:User=ecls_uat:Password=\$\{ALIAS\=mysql_ecls\}:characterEncoding=UTF-8:databaseName=foStatisticRelease" mysql_ecls
set domain.resources.jdbc-connection-pool.mysql_ecls.connection-validation-method=auto-commit
set domain.resources.jdbc-connection-pool.mysql_ecls.is-connection-validation-required=true
create-jdbc-resource --connectionpoolid mysql_ecls jdbc/ecls

ping-connection-pool mysql_ecls


#
# scripts
#
rentalfront/bin/switch-datacenter -a nsg
fareoffice/bin/rfgf-switch-datacenter -a nsg
