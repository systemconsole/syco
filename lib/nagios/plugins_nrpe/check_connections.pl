#!/usr/bin/perl -w
## Nagios Plugin for checking the number of established network connections
## You can check the number of established network connections of a specific user
## or the number of network connections of a given command. Those two options
## can be combined.
##
## Note: This script uses lsof with sudo.
## Make sure your /etc/sudoers is properly configured.
## For example put the following line into /etc/sudoers
##      nagios      ALL=NOPASSWD: /usr/sbin/lsof
## Please refer to the manpages for further options.
##
## Copyright 2007 Benjamin Hackl
## Released under the LGPL,
## visit http://www.gnu.org/licenses/lgpl.html for details.

use POSIX;
use strict;
use Getopt::Long;

use vars qw($opt_V $opt_h $PROGNAME $opt_w $opt_c $opt_t $opt_u $opt_C $opt_a $status);
use lib  "/usr/lib64/nagios/plugins/";
use utils qw(%ERRORS &print_revision &support &usage );
use vars qw($PROGNAME);

my $count = 0;
my $exit_mode;
my $lsof_bin = "sudo /usr/sbin/lsof";
my $lsof_option = '';

sub print_help ();
sub print_usage ();
sub process_arguments ();

Getopt::Long::Configure('bundling');
$status = process_arguments();
if ($status) {
   print("ERROR: processing arguments\n");
   exit $ERRORS{"UNKNOWN"};
}

$SIG{'ALRM'} = sub {
   print("ERROR: Timed out.");
   exit $ERRORS{"WARNING"};
};

if (!$opt_u && !$opt_C) {
  print("ERROR: specify either a loginname or a command.\n");
  exit $ERRORS{"WARNING"};
}

if ($opt_u && $opt_u !~ m/\d+|\w+/) {
  print("ERROR: user must be an uid or a login name.\n");
  exit $ERRORS{"WARNING"};
}

##
if ($opt_u) {
  $lsof_option .= "-u $opt_u ";
}
if ($opt_C) {
  $lsof_option .= "-c $opt_C ";
}

if ($opt_a) {
  $lsof_option .= "-i $opt_a ";
} else {
  $lsof_option .= "-i ";
}

if (!(open(LSOF, "$lsof_bin -n -P -a $lsof_option | "))) {
        print "ERROR: could not open lsof!\n";
        exit $ERRORS{'UNKNOWN'};
}


while (<LSOF>) {
        chomp();
        if (/ESTABLISHED/) {
                # only count established connections
                $count++;
        }
}
close(LSOF);

if ($count >= $opt_c) {
        print "CRITICAL - ";
        $exit_mode = $ERRORS{"CRITICAL"};
} elsif( $count >= $opt_w) {
        print "WARNING - ";
        $exit_mode = $ERRORS{"WARNING"};
} else {
        print "OK - ";
        $exit_mode = $ERRORS{"OK"};
}
print "Established connections: $count | Connections=$count;$opt_w;$opt_c;0;\n";
exit $exit_mode;


sub process_arguments() {
   GetOptions
             ("V"   => \$opt_V, "version"    => \$opt_V,
              "h"   => \$opt_h, "help"       => \$opt_h,
              "w=i" => \$opt_w, "warning=i"  => \$opt_w,   # warning if above this number
              "c=i" => \$opt_c, "critical=i" => \$opt_c,   # critical if above this number
              "t=i" => \$opt_t, "timeout=i"  => \$opt_t,
              "u=s" => \$opt_u, "user=s"     => \$opt_u,   # username or uid
              "C=s" => \$opt_C, "command=s"  => \$opt_C,   # programm name
              "a=s" => \$opt_a, "address=s"  => \$opt_a    # Address to filter by
              );

   if ($opt_V) {
     print_revision($PROGNAME, '$Revision: 1.1 $ ');
     exit $ERRORS{'OK'};
   }
   if ($opt_h) {
     print_help();
     exit $ERRORS{'OK'};
   }
   unless (defined $opt_t) {
     $opt_t = $utils::TIMEOUT; # default timeout
   }
   unless (defined $opt_w && defined $opt_c) {
     print_usage();
     exit $ERRORS{'UNKNOWN'};
   }
   if ($opt_w >= $opt_c) {
     print("Warning (-w) cannot be greater or equal than critical (-c)!\n");
     exit $ERRORS{'UNKNOWN'};
   }
   if (defined $opt_w && !defined $opt_c) {
     print("Need critical(-c) when warning(-w) is set.\n");
     exit $ERRORS{'UNKNOWN'};
   } elsif(!defined $opt_w && defined $opt_c) {
     print("Need warning(-w) when critical(-c) is set.\n");
     exit $ERRORS{'UNKNOWN'};
   }

   return $ERRORS{'OK'};
}

sub print_usage() {
   print "Usage: $PROGNAME -w <warn> -c <crit> [-u loginname|uid] [-C command name] [-t <timeout>] [-a [protocol][\@hostname|hostaddr][:service|port]] [-v verbose]\n";
}

sub print_help() {
   print_revision($PROGNAME,'$Revision: 1.1 $');
   print "-w (--warning)  Generates a warning if connections are above this value.\n";
   print "-c (--critical) Generates a critical alert if connections are above this value.\n";
   print "-u (--user)     Specifies the loginname or uid.\n";
   print "-a (--address)  Specifies an optional address to filter on. For more syntax info, see man lsof -i arg.";
   print "-C (--command)  Specifies the name of the command executed.\n";
   print "-t (--timeout)  Plugin timeout in seconds (default: $utils::TIMEOUT)\n";
   print "-h (--help)     This screen.\n";
   print "-V (--version)  Plugin Version.\n";
   print "\n\n";
   print "Note: -w and -c are required arguments given in numbers.\n";
   print "      either -u or -C is required. -u can be given as a loginname or as an uid.\n";
   print "      -C can be given as the full command name or as a part of the command.\n";
   print "example:\n";
   print " $PROGNAME -w 100 -c 120 -u apache\n";
   print "Generates a warning if the user apache has more than 100 established connections\n";
   print "and an error if the established connection count is above 120.\n";
   print " $PROGNAME -w 100 -c 120 -c httpd\n";
   print "Generates a warning if the process matching the name 'httpd' has more than 100\n";
   print "established connections and an error if this values is above 120.\n\n";
   support();
}

# [EOF]
