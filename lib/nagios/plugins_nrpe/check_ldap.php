#!/usr/bin/php -q

<?php
// Source: https://www.monitoringexchange.org/inventory/Check-Plugins/Software/LDAP/check_ldap_bind
// Checks if a user can bind with ldap (only tested on Active Directory 2003)
// Exit Errorlevels: 0=OK, 1=Warning, 2=Critical, 3=Unknown
error_reporting(E_ERROR | E_PARSE);

// Help information
$help = "LDAP Bind check plugin for nagios\n" .
        "----------------------------------\n" .
        "Usage: check_ldap_auth -H <host> [-p <port>] -U username -P password\n" .
        "--help\n" .
        "  print this help message\n" .
        "-H\n" .
        "  name or IP address of host to check\n" .
        "-U\n" .
        "  username to bind with ldap\n" .
        "-P\n" .
        "  password for the username to bind with\n" .
        "-p\n" .
        "  port number (optional, defaults to 389)\n";

// Print help if no argument is specified
if ($argc <= 1) {
  fwrite(STDOUT,$help);
  exit(0);
}

$options = getopt("h:H:p:U:P:");

if ($options['h']) {
  fwrite(STDOUT,$help);
  exit(0);
} 

if ($options['H']) {
  $ldaphost = $options['H']; 
} else {
  fwrite(STDOUT,"Missing hostname/ip (-H)\n");
  exit(3);
}

if ($options['p']) {
  $ldapport = $options['p']; 
} else {
  $ldapport = "389";
}

if ($options['U']) {
  $ldapusername = $options['U']; 
} else {
  fwrite(STDOUT,"Missing username (-U)\n");
  exit(3);
}

if ($options['P']) {
  $ldappassword = $options['P']; 
} else {
  fwrite(STDOUT,"Missing password (-P)\n");
  exit(3);
}

// Connecting to LDAP
$ldapconn = ldap_connect($ldaphost, $ldapport); 
       
if ($ldapconn) {

  // binding to ldap server
  // we have to suppress the the ldap_bind with @ as it returns PHP warnings. 
  $ldapbind = @ldap_bind($ldapconn, $ldapusername, $ldappassword);

  // verify binding (auth)
  if ($ldapbind) {
    // Close ldap connection
    ldap_close($ldapconn);
    fwrite(STDOUT,"LDAP bind successful\n");
    exit(0);
  } else {
    // Close ldap connection
    ldap_close($ldapconn);
    fwrite(STDOUT,"LDAP bind failed\n");
    exit(2);
  }

}
?>
