yum -y update
yum -y install git policycoreutils-python yum-presto man mlocate wget
yum erase atmel-firmware b43-openfwwf ipw2100-firmware ipw2200-firmware ivtv-firmware iwl1000-firmware iwl3945-firmware iwl4965-firmware iwl5000-firmware iwl5150-firmware iwl6000-firmware iwl6050-firmware libertas-usb8388-firmware zd1211-firmware xorg-x11-drv-ati-firmware
rm -rf /opt/syco
scp -r root@10.100.111.231:/opt/syco /opt
/opt/syco/bin/syco.py install-syco
/opt/syco/bin/syco.py change-env tp


To readmine??
https://redmine.fareoffice.com/projects/sysops/wiki/TelefonplanNetworkSchema
PCI server asset page??

|Hostname                   |RAM  |CPU|Back-ip   |Front-ip|PCI scope|Hardware|Comment       |
|[[fo-tp-fw]]		        |     |   |10.100.0.1|        |         |HP 380  |Firewall      |
|[[fo-tp-sw2|fo-tp-sw2-dmz]]|     |   |10.100.0.2|        |         |        |Switch        |
|[[fo-tp-phone]]            |     |   |10.100.0.3|        |         |        |HP            |
|[[fo-tp-system]]           |     |   |          |        |         |        |              |
|                           |     |   |          |        |         |        |              |
|[[vh01-tp]]                |     |   |          |        |         |        |Server - host |
|+[[install-tp]]            |768  |2  |          |        |         |        |Server - guest|
|+[[ntp-tp]]                |768  |1  |          |        |         |        |Server - guest|
|+[[ldap-tp]]               |768  |1  |          |        |         |        |Server - guest|
|+[[mailrelay-tp]]          |768  |1  |          |        |         |        |Server - guest|
|+[[dns-tp]]                |768  |1  |          |        |         |        |Server - guest|
|+[[log-tp]]                |768  |1  |          |        |         |        |Server - guest|
|+[[bounce-tp]]             |768  |1  |          |        |         |        |Server - guest|
|+[[monitor-tp]]            |768  |1  |          |        |         |        |Server - guest|
|+[[scan-tp]]               |768  |1  |          |        |         |        |Server - guest|
|+[[file-tp]]               |768  |1  |          |        |         |        |Server - guest|
|+[[mail-tp]]               |7168 |4  |          |        |         |        |Server - guest|
|+[[vcs-tp]]                |768  |1  |          |        |         |        |Server - guest|
|TOTALT                     |15616|16 |          |        |         |        |              |
|                           |     |   |          |        |         |        |              |
|[[vh02-tp]]                |     |   |          |        |         |        |Server - host |
|+[[mysql1-tp]]             |6144 |4  |          |        |         |        |Server - guest|
|+[[mysql2-tp]]             |2048 |4  |          |        |         |        |Server - guest|
|+[[fpweb-int-tp]]          |2048 |4  |          |        |         |        |Server - guest|
|+[[fpweb-stable-tp]]       |2048 |4  |          |        |         |        |Server - guest|
|+[[fpweb-uat-tp]]          |2048 |4  |          |        |         |        |Server - guest|
|TOTALT                     |14336|20 |          |        |         |        |              |
|                           |     |   |          |        |         |        |              |
|[[vh03-tp]]                |     |   |          |        |         |        |Server - host |
|+[[rfweb-int-tp]]          |4096 |4  |          |        |         |        |Server - guest|
|+[[rfweb-stable-tp]]       |4096 |4  |          |        |         |        |Server - guest|
|+[[rfweb-uat-tp]]          |4096 |4  |          |        |         |        |Server - guest|
|TOTALT                     |12288|6  |          |        |         |        |Server - guest|
|                           |     |   |          |        |         |        |Server - guest|
|+[[vh04-tp]]               |     |   |          |        |         |        |Server - host |
|+[[backup-tp]]             |1024 |4  |          |        |         |        |Server - guest|
|+[[foweb-int-tp]]          |4096 |2  |          |        |         |        |Server - guest|
|+[[foweb-uat-tp]]          |4096 |2  |          |        |         |        |Server - guest|
|+[[dalitst-tp]]            |1024 |8  |          |        |         |        |Server - guest|
|+[[mahetst-tp]]            |1024 |8  |          |        |         |        |Server - guest|
|+[[build-tp]]              |4096 |8  |          |        |         |        |Server - guest|
|TOTALT                     |15360|32 |          |        |         |        |       |

h1. Telecity-DC

|Hostname             |RAM   |CPU|Back-ip   |Front-ip|PCI scope|Hardware         |Comment              |
|[[fo-tc-fw1]]        |      |   |          |        |X        |Clavister SG3200 |Firewall             |
|[[ds-fo-tc-ext1]]    |      |   |          |        |X        |HP Switch 2626   |Switch               |
|[[ds-fo-tc-int1]]    |      |   |          |        |X        |HP Switch 2650   |Switch               |
|[[fo-tc-switch1]]    |      |   |          |        |X        |Linksys sfe2000  |Switch               |
|[[fp-tc-vm01]]       |      |   |          |        |X        |HP 380dl         |Server               |
|+-[[fp-tc-web1]]     |      |   |          |        |X        |HP 380dl         |Server               |
|+-[[fp-tc-db1]]      |      |   |          |        |X        |HP 380dl         |Server               |
|[[fp-tc-log]]        |      |   |          |        |X        |HP 360           |Server               |
|[[fo-tc-php1]]       |      |   |          |        |         |HP 360           |Server               |
|[[fo-tc-vm01]]       |      |   |          |        |         |HP 380dl         |Server               |
|+-[[fo-tc-web1]]     |      |   |          |        |         |HP 380dl         |Server               |
|+-[[fo-tc-db1]]      |      |   |          |        |         |HP 380dl         |Server               |
|[[fo-tc-failsafe]]   |      |   |          |        |         |                 |Power failover switch|
|                     |      |   |          |        |         |                 |                     |
|[[vh01-tc]]          |      |   |          |        |         |                 |                     |
|+[[install-tc]]      |768   |2  |          |        |         |                 |                     |
|+[[ntp-tc]]          |768   |1  |          |        |         |                 |                     |
|+[[mailrelay-tc]]    |768   |1  |          |        |         |                 |                     |
|+[[ldap-tc]]         |768   |1  |          |        |         |                 |                     |
|+[[dns-tc]]          |768   |1  |          |        |         |                 |                     |
|+[[log-tc]]          |768   |1  |          |        |         |                 |                     |
|+[[bounce-tc]]       |768   |1  |          |        |         |                 |                     |
|+[[monitor-tc]]      |768   |1  |          |        |         |                 |                     |
|+[[scan-tc]]         |768   |1  |          |        |         |                 |                     |
|+[[redmine-tc]]      |3072  |2  |          |        |         |                 |                     |
|+[[mysql-tc]]        |6144  |4  |          |        |         |                 |                     |
|+[[rvweb-tc]]        |4096  |4  |          |        |         |                 |                     |
|+[[fpweb-tc]]        |4096  |4  |          |        |         |                 |                     |
|+[[foweb-tc]]        |4096  |4  |          |        |         |                 |                     |
|+[[dalitst-tc]]      |2048  |8  |          |        |         |                 |                     |
|TOTALT               |30464 |28 |          |        |         |                 |                     |
|                     |      |   |          |        |         |                 |                     |
|[[vh02-tc]]          |      |   |          |        |         |                 |                     |
|+[[backup-tc]]       |3072  |4  |          |        |         |                 |                     |
|TOTALT               |3072  |4  |          |        |         |                 |                     |
|                     |      |   |          |        |         |                 |                     |

h1. Oderland-DC
|Hostname                          |RAM   |CPU|Back-ip   |Front-ip|PCI scope|Hardware         |Comment              |
|[[fo-oderland]]                   |NA    |NA |NA        |        |         |NA               |Webhotell            |
|[[sysops:domains|nsg dns server]] |NA    |NA |NA        |        |X        |NA               |                     |

