#Develop envi
#fetch from dev servers to file-cow

rsync -avz -e ssh root@192.168.3.21:/opt/fareoffice/AutomaticBackups/develop/fo-dev-mysql/ /opt/backup/AutomaticBackups/develop/fo-dev-mysql2/
logger backupen hämtat från fo-dev-mysql ok

rsync -avz -e ssh root@192.168.3.20:/opt/glassfish/domains/domain1/ /opt/backup/AutomaticBackups/develop/fo-dev-glassfish2/
logger backupen hämtat från fo-dev-glassfish ok

rsync -avz -e ssh root@192.168.3.11:/opt/fareoffice/AutomaticBackups/develop/fp-dev-mysql/ /opt/backup/AutomaticBackups/develop/fp-dev-mysql2/
logger backupen hämtat från fp-dev-mysql

rsync -avz -e ssh root@192.168.3.10:/opt/glassfish/domains/domain1/ /opt/backup/AutomaticBackups/develop/fp-dev-glassfish2/
logger backupen hämtat från fp-dev-glassfish


