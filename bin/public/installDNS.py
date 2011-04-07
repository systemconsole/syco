#! /usr/bin/env python


import ConfigParser
import os
import time
import stat
import shutil
import traceback
import sys
import app
import general
import version
import datetime
from datetime import date
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
  

def install_dns(args):
  '''
  Apache installation
  
  '''
 # self.prop.init_properties(args[1])
 # version_obj=version.Version("installDns" + self.prop.environment, self.SCRIPT_VERSION)
 # version_obj.check_executed()

  if os.path.exists('/etc/ssl/ca/private/ca.key'):

    app.print_verbose("DNS Master is already installed")

  else:

    #making folders
    os.system("yum install bind bind-chroot bind-libs bind-utils caching-nameserver")
    os.chdir("/tmp/")

    #Setting upp dns key generating and the pasting in to file
    #If the new key excists then now new key is genertaed
  SYCO_PATH = app.SYCO_PATH
  if os.path.exists('/var/named/chroot/etc/rndc_new.key'):
        N=5
        f=open("/var/named/chroot/etc/rndc_new.key")
        n = open("/var/named/chroot/etc/named.conf","w") #open for append
        o = open("/var/named/chroot/etc/rndc.key","w")
        n.write("#named DNS generated from SYCO DO NOT EDIT")
	o.write("#named DNS generated from SYCO DO NOT EDIT")

        for i in range(N):
            #line=f.next().strip()
            #o.write (line+"\n")
            #n.write (line+"\n")
            #app.print_verbose(line)
            print i
        f.close()
        n.close()
        o.close()
  else:
	os.chdir("/tmp")
        os.system("rndc-confgen > /var/named/chroot/etc/rndc_new.key")
        general.shell_exec("chown root:named rndc.key")

        N=5
        f=open("/var/named/chroot/etc/rndc_new.key")
        n = open("/var/named/chroot/etc/named.conf","w") #open for append
        o = open("/var/named/chroot/etc/rndc.key","w")
        n.write("#named DNS generated from SYCO DO NT EDIT")
	o.write("#named DNS generated from SYCO DO NT EDIT")	

        for i in range(N):
            line=f.next().strip()
            o.write (line+"\n")
            n.write (line+"\n")
            print line
            i = i +1
        f.close()
        n.close()
        o.close()



  #time_ut =  int(time.time()*100)
  #serial = str(time_ut)


    #Generating config file
  config = ConfigParser.SafeConfigParser()
  
  config.read(SYCO_PATH + 'var/dns/zone.cfg')
  dnsrange = config.get('config', 'range')
  forward1 = config.get('config', 'forward1')
  forward2 = config.get('config', 'forward2')
  ipmaster = config.get('config', 'ipmaster')
  ipslave = config.get('config', 'ipslave')
  #role =  config.get('config','role')
  role  =str(args[1])
  
    #Setting upp named.con file for dns server
  o = open("/var/named/chroot/etc/named.conf","a") #open for append
  for line in open(SYCO_PATH + "var/dns/"+role+"-named.conf"):
        line = line.replace("$IPSLAVE$",ipslave)
        line = line.replace("$IPMASTER$",ipmaster)
        line = line.replace("$RANGE$",dnsrange)
        line = line.replace("$FORWARD1$",forward1)
        line = line.replace("$FORWARD2$",forward2)
        
        o.write(line)
  o.close()    

    #Setting upp dns zone and recursiv file for config
  #Regex to find serial
  p = re.compile('[\s]*([\d]*)[\s]*[;][\s]*Serial' )

   #get all arecord and putting them into the file
  for zone in config.options('zone'):
                rzone = config.get('zone',zone)
                #Create zone files for every zone in file
                o = open("/var/named/chroot/var/named/data/" + zone + ".zone","w") #open for append
                for line in open(SYCO_PATH + "var/dns/template.zone"):
                    line = line.replace("$IPMASTER$",ipmaster)
                    line = line.replace("$IPSLAVE$",ipslave)
                    line = line.replace("$NAMEZONE$",zone)
                    serial = p.findall (line)                    
                    if len(serial) > 0:
                        line = str(int(serial[0])+1)+"   ;   Serial\n"
                    o.write(line + "\n")
               

                 #Wrinting out arecord to zone file
                for option in config.options(zone+"_arecords"):
                       o.write (option + "." + zone+ "."+ "     IN     A    "+ config.get(zone+"_arecords",option)+" \n")
                       print option+"."+ zone+"."+ "A"+ config.get(zone+"_arecords",option)+"."

                if zone == app.get_domain():
                    servers = app.get_servers()
                    for server in servers:
                        o.write (server + "." + zone+ "."+ "     IN     A    "+app.get_ip(server) +" \n")
                        print server + app.get_ip(server)
                    
                for option in config.options(zone+"_cname"):
                       o.write (option+ "     IN    CNAME   "+ config.get(zone+"_cname",option)+"\n")
                       print option+"."+ zone+ "    IN    CNAME   "+ config.get(zone+"_cname",option)+"."+zone

		o.close()                
		#Creating recursiv zone file
                o = open("/var/named/chroot/var/named/data/" + rzone + ".zone","w") #open for append
                for line in open(SYCO_PATH + "var/dns/recursiv-template.zone"):
                        line = line.replace("$IPMASTER$",ipmaster[::-1])
                        line = line.replace("$IPSLAVE$",ipslave[::-1])
                        line = line.replace("$NAMEZONE$",zone)
                        line = line.replace("$RZONE$",rzone)
                        serial = p.findall (line)
                        if len(serial) > 0:
                            line = str(int(serial[0])+1)+"   ;   Serial\n"
                        o.write(line + "\n")
                o.close()

                #Adding the created zone files to the namd.con file
                o = open("/var/named/chroot/etc/named.conf","a") #open for append
                for line in open(SYCO_PATH + "var/dns/"+role+"-zone.conf"):
                    line = line.replace("$IPMASTER$",ipmaster)
                    line = line.replace("$IPSLAVE$",ipslave)
                    line = line.replace("$NAMEZONE$",zone)
                    line = line.replace("$RZONE$",rzone)
                    o.write(line + "\n")
                o.close()


               

   #Fixing serial number on tenplates that are redu to use for next time
  #On recursive look up
  os.system("mv "+ SYCO_PATH +"var/dns/recursiv-template.zone /tmp/recursiv-template.zone")
  o = open(SYCO_PATH +"var/dns/recursiv-template.zone","w") #open for append
  for line in open("/tmp/recursiv-template.zone"):
    serial = p.findall (line)
    if len(serial) > 0:
        line = str(int(serial[0])+1)+"   ;   Serial\n"
    o.write(line)
  o.close()

  #fixing serial nummer on zone files

  os.system("mv "+SYCO_PATH +"var/dns/template.zone /tmp/template.zone")
  o = open(SYCO_PATH +"var/dns/template.zone","w") #open for append
  for line in open("/tmp/template.zone"):
    serial = p.findall (line)
    if len(serial) > 0:
        line = str(int(serial[0])+1)+"   ;   Serial\n"
    o.write(line)
  o.close()
  general.shell_exec("/etc/init.d/named restart")
 
