#!/usr/bin/env python
'''
Test cases for config.py

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Test"

import unittest
import os

import config

# Initialize config module.
test_path = os.path.realpath(__file__)
test_path = os.path.split(test_path)[0] + "/"
config.load(test_path)

class TestGeneralConfig(unittest.TestCase):

    def test_config(self):
       self.assertEqual(config.get_servers(), ['syco-mysql-primary', 'syco-mysql-secondary', 'syco-install', 'syco-ldap', 'syco-vh01', 'syco-ntp'])
       self.assertEqual(config.get_hosts(), ['syco-vh01'])

    def test_general(self):
        general = config.general

        self.assertEqual(general.get_installation_server(), "syco-install")
        self.assertEqual(general.get_installation_server_ip(), "10.0.0.3")
        self.assertEqual(general.get_front_gateway_ip(), "10.0.1.1")
        self.assertEqual(general.get_back_gateway_ip(), "10.0.0.1")
        self.assertEqual(general.get_front_netmask(), "255.255.255.0")
        self.assertEqual(general.get_back_netmask(), "255.255.255.0")
        self.assertEqual(general.get_external_dns_resolver(), "8.8.8.8")
        self.assertEqual(general.get_internal_dns_resolvers(), "10.0.0.100")
        self.assertEqual(general.get_resolv_domain(), "syco.com")
        self.assertEqual(general.get_resolv_search(), "syco.com")
        self.assertEqual(general.get_ldap_server(), "syco-ldap")
        self.assertEqual(general.get_ldap_server_ip(), "10.0.0.4")
        self.assertEqual(general.get_ldap_hostname(), "ldap.syco.com")
        self.assertEqual(general.get_ldap_dn(), "dc=syco,dc=com")
        self.assertEqual(general.get_ntp_server(), "syco-ntp")
        self.assertEqual(general.get_ntp_server_ip(), "10.0.0.5")
        self.assertEqual(general.get_mail_relay_domain_name(), "mail-relay.syco.com")
        self.assertEqual(general.get_cert_server(), "syco-install")
        self.assertEqual(general.get_cert_server_ip(), "10.0.0.3")
        self.assertEqual(general.get_mysql_primary_master_ip(), "10.0.0.6")
        self.assertEqual(general.get_mysql_secondary_master_ip(), "10.0.0.7")
        self.assertEqual(general.get_country_name(), "SE")
        self.assertEqual(general.get_state(), ".")
        self.assertEqual(general.get_locality(), "Stockholm")
        self.assertEqual(general.get_organization_name(), "The System Console Project")
        self.assertEqual(general.get_organizational_unit_name(), "System Console")
        self.assertEqual(general.get_admin_email(), "syco@cybercow.se")

    def test_host_vh01_install(self):
        host = config.host("syco-vh01")

        self.assertEqual(host.get_front_ip(), None)
        self.assertEqual(host.get_back_ip(), "10.0.0.2")
        self.assertEqual(host.get_back_mac(), "xx:xx:xx:xx:xx:xx")
        self.assertRaises(config.ConfigException, host.get_ram)
        self.assertRaises(config.ConfigException, host.get_cpu)
        self.assertRaises(config.ConfigException, host.get_disk_var)
        self.assertRaises(config.ConfigException, host.get_boot_device)
        self.assertEqual(host.get_boot_device("hda"), "hda")
        self.assertEqual(host.is_host(), True)
        self.assertEqual(host.has_guests(), True)
        self.assertEqual(host.get_commands(), ['syco iptables-setup', 'syco hardening'])
        self.assertEqual(host.get_guests(), ['syco-install', 'syco-ntp'])
        self.assertEqual(host.get_backup_pathes(), ['/etc/', '/tmp/'])


    def test_host_syco_install(self):
        host = config.host("syco-install")

        self.assertEqual(host.get_front_ip(), "10.0.1.3")
        self.assertEqual(host.get_back_ip(), "10.0.0.3")
        self.assertRaises(config.ConfigException, host.get_back_mac)
        self.assertEqual(host.get_ram(), "1024")
        self.assertEqual(host.get_cpu(), "1")
        self.assertEqual(host.get_disk_var(), "40")

        self.assertRaises(config.ConfigException, host.get_boot_device)
        self.assertEqual(host.get_boot_device("hda"), "hda")
        self.assertEqual(host.is_host(), False)
        self.assertEqual(host.has_guests(), False)
        self.assertEqual(host.get_commands(), ['syco iptables-setup', 'syco hardening'])
        self.assertEqual(host.get_guests(), [])
        self.assertEqual(host.get_backup_pathes(), ['/etc/'])

if __name__ == '__main__':
    unittest.main()
