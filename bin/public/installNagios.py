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

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script. 
  
  '''
  commands.add("install-nagios",   install_nagios,  help="Install Nagios server on the server.")
  

def install_nagios(args):
  '''
  Apache installation
  
  '''

  if os.path.exists('/etc/nagios/nagios_2.cfg'):

    app.print_verbose("Nagios server is already installed")

  else:

    #Nagios is not installed installing
    general.shell_exec("yum install nagios nagios-plugins nagios-plugins-all nagios-plugins-nrpe nagios-devel httpd -y")


    #Setting upp apache for nagios FUNKAR EJ 100
    #general.set_config_property("/etc/httpd/conf.d/nagios.conf", '^.*allow from.*',  'allow from all')


    #Setting upp nagios users
    #general.shell_exec("htpasswd -c /etc/nagios/passwd matte")

   

    general.set_config_property("/etc/nagios/nagios.cfg", '^.*cfg_file\=\/etc\/nagios\/commands\.cfg.*',  '#cfg_file=/etc/nagios/commands.cfg')
    general.set_config_property("/etc/nagios/nagios.cfg", '^.*cfg_file\=\/etc\/nagios\/localhost\.cfg.*',  '#cfg_file=/etc/nagios/localhost.cfg')
    general.set_config_property("/etc/nagios/nagios.cfg", '^.*cfg_dir\=\/etc\/nagios\/fosh\/.*',  'cfg_dir=/etc/nagios/fosh/')


    #######################
    #Set up config file
      #Generating config file
    config = ConfigParser.SafeConfigParser()

    config.read('/opt/syco/var/nagios/nagios.cfg')
    general.shell_exec("mkdir /etc/nagios/fosh")
    #Server group list
    server_group =[]

    #######################3
    #Generate host from config file
    for option in config.options("servers"):
        o = open("/etc/nagios/fosh/" + option + ".cfg","w") #creating new host file
        o.write("#host generated from fosh\n")
        o.write( "define host{\n")
        o.write( "use  inhouse ;template\n")
        o.write( "host_name    "+ option+"\n")
        o.write( "alias    "+option+"\n")
        o.write( "address  "+config.get('servers',option)+"\n")
        o.write( "}\n")
        o.close()

        #adding hos to group
        server_group.append(option)


    #########################
    #Creating host file and adding servers
    o = open("/etc/nagios/fosh/group.cfg","w") #creating new host file
    o.write("#hostgroup generated from fosh\n")
    o.write( "define hostgroup{\n")
    o.write( "hostgroup_name   Servers \n")
    o.write( "alias    Servers\n")
    o.write("members ")
    for option in server_group:
        print option
        
        o.write(  option + ",")
    o.write( "\n}\n")
    o.close()








    #Restaring services
    general.shell_exec('/usr/sbin/nagios -v /etc/nagios/nagios.cfg')
    general.shell_exec('/etc/init.d/nagios restart')
    general.shell_exec('/etc/init.d/httpd restart')