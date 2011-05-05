#! /usr/bin/env python
'''
Install DNS server.

This server will be installed with the chrooted bind dns server.
The script mwill read DNS config files from syco/var/dns
and generate dns enteries for server in config files.

# Will be stored.
/etc/important_file.txt
# Will be ignored.
/etc/NoBackup/very_large_unimportant_file.zip

install-dns
--------------
MASTER
The installation will install the master BIND dns server from configfiles.
The master dns server will be sett upp so that the slave DNS server are allowd to connect to
the Master DNS and transfer DNS record from the master

SLAVE
The installation of the slave DNS server will installe the slave dns server from configfiles.
The slave DNS server will conenct to the master dns server and retrive changes to the DNS records.

SERIAL
So that that both dns server now witch is the newest dns record all changes to the DNS have to be
updaed with an serial number. Then the script is run the serial number will update is self and the templates used to
generate the config files.
To reset the serial number sett the serial number to 0 in the master-template.zone and the slave-template.zone


RDNC KEY
So that the slave is allowed to connect to the master DNS server and retrive the the new DNS update they master and the slave has to have the same key.
Theis key in generated the first time the master dns server is installed.
The slave server the used ssh to retrive the key from the master server.


Configuration
-------------

In the file zone.cfg the main config options is inserted

[config]
range:10.100.100.0/24 <-- Range of server network
localnet:192.168/16 <-- Range oh the client network alloed to to recursive reqest
forward1:8.8.8.8 <-- DNS forwarder 1
forward2:4.4.4.4 <-- DNS forwarder 2
ipmaster:10.100.100.10 <-- IP of master DNS
ipslave:10.100.100.241 <-- IP of slave DNS

#Choose witch location to be active
#in you cnames set $DATA_CENTER$ and it will be changed
data_center:nsg

#Zone to be used
#Create an file called exempel.org in this folder that contains dns records
[zone]
fareonline.net:100.100.10
farepayment.com:192.168.0.0

ZONE Config
----------------
To edit zones to the dns name create oen file with teh same name as the dns name.
For exempel fareonline.net create the file called fareonline.net.
In that file the create two blocks


[fareonline.net_arecords]
www:178.78.197.210

[fareonline.net_cname]
webb:www

The first one is for A records and the second one is for cnames.
The script will generate dns files from the enteries.


INTERNAL VIEW
-----------------
The DNS server support differt views so that the same dns name van be pinted to differt ip dependning if you are qesting the DNS server from you local network
ore the internet.
As defult all entories will be the same if you not specifi in the zone file the differt name.

To add internal ip to be used add in you configfile for you dns name

[internal_fareonline.net_arecords]
www:10.100.0.4

[internal_fareonline.net_cname]
mail:fo-tp-mail

The script will then generate this config to be used for internal view and the other will to be used for external view.


PRIMARY DATACENTER
----------------
The DNS server support changing primary datacenter wen generating the files.
By in the configfile setting

data_center:nsg the datacenter named nsg will be used.

1. Sett upp an a record to both locations
nsg-server.fareonline.net:10.100.0.1
tc-server.fareonline.net:99.100.100.1

2. Set upp an cname to the a record
server:nsg-server

3. Set upp for auto changing datacenter
chnage the cname record above to
server:$DATA_CENTER$-server

READING
----------------
http://www.wains.be/index.php/2007/12/13/centos-5-chroot-dns-with-bind/

'''

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"




import ConfigParser
import os
import app
import general
import re

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script. 
  
  '''
  commands.add("install-dns",   install_dns,  help="Install DNS server use command 'install-dns master/slave' ")

def _copy_rndc():
    '''
    Copy rndc key from the keyfile into named.conf file.
    named.conf file. The rndc key is used for connection between two servers

    The generated rndc key files contains many commands but we only want the key
    So for onlyt getting the key we only steel the first 5 rows
    '''
    N = 5
    f = open("/var/named/chroot/etc/rndc_new.key")
    n = open("/var/named/chroot/etc/named.conf","w") #open for append
    o = open("/var/named/chroot/etc/rndc.key","w")
    n.write("#named DNS generated from SYCO DO NOT EDIT\n")
    o.write("#named DNS generated from SYCO DO NOT EDIT\n")
    for i in range(N):
        line=f.next().strip()
        o.write (line + "\n")
        n.write (line + "\n")
        app.print_verbose(line)
    f.close()
    n.close()
    o.close()



def _add_serial(name):
  '''
  fixing upp so that serial number are working be adding one and add it to the tamplate used to generat
  zone files.
  '''
  p = re.compile('[\s]*([\d]*)[\s]*[;][\s]*Serial')
  os.system("mv "+ app.SYCO_PATH +"var/dns/"+name+".zone /tmp/"+name+".zone")
  o = open(app.SYCO_PATH +"var/dns/"+name+".zone","w") #open for append
  for line in open("/tmp/"+name+".zone"):
    serial = p.findall (line)
    if len(serial) > 0:
        line = str(int(serial[0])+1)+"   ;   Serial\n"
    o.write(line)
  o.close()
 
def install_dns(args):
  '''
  DNS Bind 9 Chrooted installation
  This will install the dns server on the host chrooted.
  This command is used only for Centos servers.
  
  '''
 
  if os.path.exists('/opt/syco/lock/dns'):
    '''
    If dns server is locked from this script
    '''
    app.print_verbose("This server has an lock stopping you from installing the DNS server ")

  else:

    '''
    Installinb server package needed for dns
    '''
    general.shell_exec("yum install bind bind-chroot bind-libs bind-utils caching-nameserver -y")
    os.chdir("/tmp/")



  '''
  Getting argument from command line
  master = setting upp master server
  slave = setting upp slave server
  '''
  role  =str(args[1])
  '''
  Reading zone.cfg file conting
  In zone.cfg is all config options neede for setting upp DNS Server
  This file is readed and the the options are saved and used when generating new config files
  '''
  config = ConfigParser.SafeConfigParser()
  config_zone = ConfigParser.SafeConfigParser()


  config.read(app.SYCO_PATH + 'var/dns/zone.cfg')
  dnsrange = config.get('config', 'range')
  forward1 = config.get('config', 'forward1')
  forward2 = config.get('config', 'forward2')
  ipmaster = config.get('config', 'ipmaster')
  ipslave = config.get('config', 'ipslave')
  localnet = config.get('config', 'localnet')
  data_center = config.get('config', 'data_center')
  #role =  config.get('config','role')

  role  =str(args[1])
  if (role != "master" or role != "slave"):
    raise Exception("You can only enter master or slave, you entered " + role)
  
  '''
  Depending if the server is an master then new rndc keys are genertaed if now old are done.
  If the server is slave the keys have to bee fetch from the master server.
  '''
  if os.path.exists('/var/named/chroot/etc/rndc_new.key'):
    _copy_rndc()
  else:
      if role =="master":
	os.chdir("/tmp")
        os.system("/usr/sbin/rndc-confgen > /var/named/chroot/etc/rndc_new.key")
        general.shell_exec("chown root:named rndc.key")
        _copy_rndc()
      else:
          os.chdir("/var/named/chroot/etc")
          os.system("scp root@" + ipmaster + ":/var/named/chroot/etc/rndc_new.key ." )
         


  def _generate_zone(location):

     p = re.compile('[\s]*([\d]*)[\s]*[;][\s]*Serial')
     if location == "internal":
          o = open("/var/named/chroot/etc/named.conf","a") #open for append
          o.write("view 'internt' {\n")
          o.write("match-clients { " + localnet + "; };\n")
          o.close()
     else:
          o = open("/var/named/chroot/etc/named.conf","a") #open for append
          o.write("view 'external' {\n")
          o.write("match-clients { any; };\n")
          o.close()

     '''
     Getting records from zone files
     and creating zone file for records
     '''


     for zone in config.options('zone'):
                rzone = config.get('zone',zone)
                config_zone.read(app.SYCO_PATH + 'var/dns/'+zone)
                print zone
                
                '''
                Crating zone file and setting right settings form zone.cfg file

                '''
                o = open("/var/named/chroot/var/named/data/" + location + "." + zone + ".zone","w") #open for write
                for line in open(app.SYCO_PATH + "var/dns/template.zone"):
                    line = line.replace("$IPMASTER$",ipmaster)
                    line = line.replace("$IPSLAVE$",ipslave)
                    line = line.replace("$NAMEZONE$",zone)
                    serial = p.findall (line)
                    print line
                    if len(serial) > 0:
                        line = str(int(serial[0]) + 1) + "   ;   Serial\n"
                    o.write(line + "\n")
                    

                 #Wrinting out arecord to zone file
                if location == "internal":
                    
                    '''
                    Getting internal network address if thy are any else go back to use external address
                    Generating A record from domain file and adding them to zone file.
                    '''
                    try:
                        config_zone.options("internal_" + zone + "_arecords")
                    except ConfigParser.NoSectionError:
                        for option in config_zone.options(zone + "_arecords"):
                            o.write (option + "." + zone + "."+ "     IN     A    " + config_zone.get(zone + "_arecords",option) + " \n")
                            print option + "." + zone+"." + "A" + config_zone.get(zone + "_arecords",option)+"."

                        if zone == app.get_domain():
                            servers = app.get_servers()
                            for server in servers:
                                o.write (server + "." + zone + "." + "     IN     A    " + app.get_ip(server) + " \n")
                                print server + app.get_ip(server)

                    else:
                         for option in config_zone.options("internal_" + zone + "_arecords"):
                            o.write (option + "." + zone + "."+ "     IN     A    " + config_zone.get("internal_" + zone + "_arecords",option) + " \n")
                            print option + "." + zone + "." + "A" + config_zone.get("internal_" + zone+"_arecords",option) + "."
                            '''
                            If domain is the same as local domain
                            Gett all ip from local servers and add them to records.
                            '''

                         if zone == app.get_domain():
                            servers = app.get_servers()
                            for server in servers:
                                o.write (server + "." + zone + "."+ "     IN     A    " + app.get_ip(server) + " \n")
                                print server + app.get_ip(server)

                    '''
                    Getting all Cnames from domain file
                    If there exist any names for internal network then they are used for inernal viem
                    Else external names are used.
                    Cnames are the added to file
                    '''
                    try:
                        config_zone.options("internal_" + zone + "_cname")
                    except ConfigParser.NoSectionError:
                         for option in config_zone.options(zone + "_cname"):
                                out = str(option) +  "     IN    CNAME   " + config_zone.get(zone + "_cname",option) + "\n"
                                out2 =out.replace('$DATA_CENTER$',data_center)
                                o.write(out2)
                                print out2
                    else:
                          for option in config_zone.options("internal_" + zone + "_cname"):
                            out= str(option) + "     IN    CNAME   "+ str(config_zone.get("internal_" + zone + "_cname",option)) + "\n"
                            out2 = out.replace('$DATA_CENTER$',data_center)
                            o.write(out2)
                            print out2


                else:
                 for option in config_zone.options(zone + "_arecords"):
                       o.write (option + "." + zone + "." + "     IN     A    " + config_zone.get(zone + "_arecords",option) + " \n")
                       print option+"." + zone + "." + "A" + config_zone.get(zone + "_arecords",option) + "."

                 for option in config_zone.options(zone+"_cname"):
                        out= str(option) + "     IN    CNAME   " + str(config_zone.get(zone + "_cname",option)) + "\n"
                        out2 = out.replace('$DATA_CENTER$',data_center)
                        o.write(out2)
                        print out2
		 o.close()
                '''
                Creating zone revers file for recursive getting if domain names.
                '''
                o = open("/var/named/chroot/var/named/data/" + location + "." + rzone + ".zone","w") #open for append
                for line in open(app.SYCO_PATH + "var/dns/recursiv-template.zone"):
                        line = line.replace("$IPMASTER$",ipmaster[::-1])
                        line = line.replace("$IPSLAVE$",ipslave[::-1])
                        line = line.replace("$NAMEZONE$", zone)
                        line = line.replace("$RZONE$" ,rzone)
                        serial = p.findall (line)
                        if len(serial) > 0:
                            line = str(int(serial[0]) + 1) + "   ;   Serial\n"
                        o.write(line + "\n")
                o.close()

                '''
                Adding the new zreated zone files to named.com to be used
                '''

                o = open("/var/named/chroot/etc/named.conf","a") #open for append
                for line in open(app.SYCO_PATH + "var/dns/" + role + "-zone.conf"):
                    line = line.replace("$IPMASTER$",ipmaster)
                    line = line.replace("$IPSLAVE$",ipslave)
                    line = line.replace("$NAMEZONE$",zone)
                    line = line.replace("$RZONE$" ,rzone)
                    line = line.replace("$LOCATION$" ,location)
                    o.write(line + "\n")
                o.close()
     '''
     Adding differin view to the config file
     '''
     if location == "internal":
          o = open("/var/named/chroot/etc/named.conf","a") #open for append
          o.write("}; \n")
          o.close()
     else:
          o = open("/var/named/chroot/etc/named.conf","a") #open for append
          o.write("};\n")
          o.close()
          '''
          Getting namd.conf tamplate and generting new file with right config.
          '''

  '''
  Setting upp named.conf with right settings
  '''
  o = open("/var/named/chroot/etc/named.conf","a") #open for append
  for line in open(app.SYCO_PATH + "var/dns/" + role + "-named.conf"):
     line = line.replace("$IPSLAVE$",ipslave)
     line = line.replace("$IPMASTER$",ipmaster)
     line = line.replace("$RANGE$",dnsrange)
     line = line.replace("$FORWARD1$",forward1)
     line = line.replace("$FORWARD2$",forward2)
     line = line.replace("$LOCALNET$",localnet)
     line = line.replace("$DOMAIN$",app.get_domain())
     o.write(line)
  o.close()
  '''
  Chnagin order if ip to match recusrsive lookup
  '''
     
 
  '''
  Generating the zone files
  IMPORTAND that  internal is first
  '''
  _generate_zone("internal")
  _generate_zone("external")
  '''
  Adding serial number to template
  '''

  _add_serial("recursiv-template")
  _add_serial("template")


  
  '''
  Restaring DNS server for action to be loaded
  '''
  general.shell_exec("/etc/init.d/named restart")
 
