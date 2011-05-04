#! /usr/bin/env python


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
  commands.add("install-dns",   install_dns,  help="Install DNS server.")

def copy_rndc():
    '''
    Copy rndc copied the rndc key from the generated file inte to
    named.conf file. The rndc key is used for connection between two servers

    The generated rndc key files contains many commands but we only want the key
    So for onlyt getting the key we only steel the first 5 rows
    '''
    N=5
    f=open("/var/named/chroot/etc/rndc_new.key")
    n = open("/var/named/chroot/etc/named.conf","w") #open for append
    o = open("/var/named/chroot/etc/rndc.key","w")
    n.write("#named DNS generated from SYCO DO NOT EDIT\n")
    o.write("#named DNS generated from SYCO DO NOT EDIT\n")
    for i in range(N):
        line=f.next().strip()
        o.write (line+"\n")
        n.write (line+"\n")
        app.print_verbose(line)
    f.close()
    n.close()
    o.close()

'''
Fixing upp so that serial number are working be adding one and add it to the tamplate used to generat
zone files.
'''

def add_serial(name,SYCO_PATH):
  p = re.compile('[\s]*([\d]*)[\s]*[;][\s]*Serial')
  os.system("mv "+ SYCO_PATH +"var/dns/"+name+".zone /tmp/"+name+".zone")
  o = open(SYCO_PATH +"var/dns/"+name+".zone","w") #open for append
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
 
  if os.path.exists('/etc/ssl/ca/private/ca.key'):
      '''
      This is not loaded now
      '''
      app.print_verbose("DNS Master is already installed")

  else:

    '''
    Installinb server package needed for dns
    '''
    os.system("yum install bind bind-chroot bind-libs bind-utils caching-nameserver")
    os.chdir("/tmp/")

  SYCO_PATH = app.SYCO_PATH

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


  config.read(SYCO_PATH + 'var/dns/zone.cfg')
  dnsrange = config.get('config', 'range')
  forward1 = config.get('config', 'forward1')
  forward2 = config.get('config', 'forward2')
  ipmaster = config.get('config', 'ipmaster')
  ipslave = config.get('config', 'ipslave')
  localnet = config.get('config', 'localnet')
  data_center = config.get('config', 'data_center')
  #role =  config.get('config','role')

  role  =str(args[1])
  
  '''
  Depending if the server is an master then new rndc keys are genertaed if now old are done.
  If the server is slave the keys have to bee fetch from the master server.
  '''
  if os.path.exists('/var/named/chroot/etc/rndc_new.key'):
    copy_rndc()
  else:
      if role =="master":
	os.chdir("/tmp")
        os.system("/usr/sbin/rndc-confgen > /var/named/chroot/etc/rndc_new.key")
        general.shell_exec("chown root:named rndc.key")
        copy_rndc()
      else:
          os.chdir("/var/named/chroot/etc")
          os.system("scp root@"+ipmaster+":/var/named/chroot/etc/rndc_new.key ." )
         


  def generate_zone(location,SYCO_PATH):

     p = re.compile('[\s]*([\d]*)[\s]*[;][\s]*Serial')
     if location == "internal":
          o = open("/var/named/chroot/etc/named.conf","a") #open for append
          o.write("view 'internt' {\n")
          o.write("match-clients { "+localnet+"; };\n")
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
                config_zone.read(SYCO_PATH + 'var/dns/'+zone)
                print zone
                
                '''
                Crating zone file and setting right settings form zone.cfg file

                '''
                o = open("/var/named/chroot/var/named/data/" +location+"." + zone + ".zone","w") #open for append
                for line in open(SYCO_PATH + "var/dns/template.zone"):
                    line = line.replace("$IPMASTER$",ipmaster)
                    line = line.replace("$IPSLAVE$",ipslave)
                    line = line.replace("$NAMEZONE$",zone)
                    serial = p.findall (line)
                    print line
                    if len(serial) > 0:
                        line = str(int(serial[0])+1)+"   ;   Serial\n"
                    o.write(line + "\n")
                    

                 #Wrinting out arecord to zone file
                if location == "internal":
                    
                    '''
                    Getting internal network address if thy are any else go back to use external address
                    Generating A record from domain file and adding them to zone file.
                    '''
                    try:
                        config_zone.options("internal_"+zone+"_arecords")
                    except ConfigParser.NoSectionError:
                        for option in config_zone.options(zone+"_arecords"):
                            o.write (option + "." + zone+ "."+ "     IN     A    "+ config_zone.get(zone+"_arecords",option)+" \n")
                            print option+"."+ zone+"."+ "A"+ config_zone.get(zone+"_arecords",option)+"."

                        if zone == app.get_domain():
                            servers = app.get_servers()
                            for server in servers:
                                o.write (server + "." + zone+ "."+ "     IN     A    "+app.get_ip(server) +" \n")
                                print server + app.get_ip(server)

                    else:
                         for option in config_zone.options("internal_"+zone+"_arecords"):
                            o.write (option + "." + zone+ "."+ "     IN     A    "+ config_zone.get("internal_"+zone+"_arecords",option)+" \n")
                            print option+"."+ zone+"."+ "A"+ config_zone.get("internal_"+zone+"_arecords",option)+"."
                            '''
                            If domain is the same as local domain
                            Gett all ip from local servers and add them to records.
                            '''

                         if zone == app.get_domain():
                            servers = app.get_servers()
                            for server in servers:
                                o.write (server + "." + zone+ "."+ "     IN     A    "+app.get_ip(server) +" \n")
                                print server + app.get_ip(server)

                    '''
                    Getting all Cnames from domain file
                    If there exist any names for internal network then they are used for inernal viem
                    Else external names are used.
                    Cnames are the added to file
                    '''
                    try:
                        config_zone.options("internal_"+zone+"_cname")
                    except ConfigParser.NoSectionError:
                         for option in config_zone.options(zone+"_cname"):
                                out = str(option) +  "     IN    CNAME   "+ config_zone.get(zone+"_cname",option) + "\n"
                                out2 =out.replace('$DATA_CENTER$',data_center)
                                o.write(out2)
                                print out2
                    else:
                          for option in config_zone.options("internal_"+zone+"_cname"):
                            out= str(option) + "     IN    CNAME   "+ str(config_zone.get("internal_"+zone+"_cname",option))+"\n"
                            out2 = out.replace('$DATA_CENTER$',data_center)
                            o.write(out2)
                            print out2


                else:
                 for option in config_zone.options(zone+"_arecords"):
                       o.write (option + "." + zone+ "."+ "     IN     A    "+ config_zone.get(zone+"_arecords",option)+" \n")
                       print option+"."+ zone+"."+ "A"+ config_zone.get(zone+"_arecords",option)+"."

                 for option in config_zone.options(zone+"_cname"):
                        out= str(option)+ "     IN    CNAME   "+ str(config_zone.get(zone+"_cname",option))+"\n"
                        out2 = out.replace('$DATA_CENTER$',data_center)
                        o.write(out2)
                        print out2
		 o.close()
                '''
                Creating zone revers file for recursive getting if domain names.
                '''
                o = open("/var/named/chroot/var/named/data/" + location +"."+ rzone + ".zone","w") #open for append
                for line in open(SYCO_PATH + "var/dns/recursiv-template.zone"):
                        line = line.replace("$IPMASTER$",ipmaster[::-1])
                        line = line.replace("$IPSLAVE$",ipslave[::-1])
                        line = line.replace("$NAMEZONE$", zone)
                        line = line.replace("$RZONE$" ,rzone)
                        serial = p.findall (line)
                        if len(serial) > 0:
                            line = str(int(serial[0])+1)+"   ;   Serial\n"
                        o.write(line + "\n")
                o.close()

                '''
                Adding the new zreated zone files to named.com to be used
                '''

                o = open("/var/named/chroot/etc/named.conf","a") #open for append
                for line in open(SYCO_PATH + "var/dns/"+role+"-zone.conf"):
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
  for line in open(SYCO_PATH + "var/dns/"+role+"-named.conf"):
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
  generate_zone("internal",SYCO_PATH)
  generate_zone("external",SYCO_PATH)
  '''
  Adding serial number to template
  '''

  add_serial("recursiv-template",SYCO_PATH)
  add_serial("template",SYCO_PATH)


  
  '''
  Restaring DNS server for action to be loaded
  '''
  general.shell_exec("/etc/init.d/named restart")
 
