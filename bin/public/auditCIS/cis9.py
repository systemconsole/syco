#!/usr/bin/env python
'''
A module to the CIS audit.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from utils import check_empty, check_equal, check_equal_re, check_equals, check_not_empty, check_return_code, print_header, view_output, print_warning, print_info

#
print_header("9 System Maintenance")

#
print_header("9.1 Verify System File Permissions)")

#
print_header("9.1.1 Verify System File Permissions (Not Scored)")
print_warning("Check manually for changed files.")
view_output("rpm -Va --nomtime --nosize --nomd5 --nolinkto")

#
print_header("9.1.2 Verify Permissions on /etc/passwd (Scored)")
check_equal('stat -c "%a %u %g" /etc/passwd | egrep "644 0 0"', "644 0 0")

#
print_header("9.1.3 Verify Permissions on /etc/shadow (Scored)")
check_equal('stat -c "%a %u %g" /etc/shadow | egrep "0 0 0"', "0 0 0")

#
print_header("9.1.4 Verify Permissions on /etc/gshadow (Scored)")
check_equal('stat -c "%a %u %g" /etc/gshadow | egrep "0 0 0"', "0 0 0")

#
print_header("9.1.5 Verify Permissions on /etc/group (Scored)")
check_equal('stat -c "%a %u %g" /etc/group | egrep "644 0 0"', "644 0 0")

#
print_header("9.1.6 Verify User/Group Ownership on /etc/passwd (Scored)")
check_equal('stat -c "%a %u %g" /etc/passwd | egrep "644 0 0"', "644 0 0")

#
print_header("9.1.7 Verify User/Group Ownership on /etc/shadow (Scored)")
check_equal('stat -c "%a %u %g" /etc/shadow | egrep "0 0 0"', "0 0 0")

#
print_header("9.1.8 Verify User/Group Ownership on /etc/gshadow (Scored)")
check_equal('stat -c "%a %u %g" /etc/gshadow | egrep "0 0 0"', "0 0 0")

#
print_header("9.1.9 Verify User/Group Ownership on /etc/group (Scored)")
check_equal('stat -c "%a %u %g" /etc/group | egrep "644 0 0"', "644 0 0")

#
print_header("9.1.10 Find World Writable Files (Not Scored)")
check_empty(
    "df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type f -perm -0002 -print"
)

#
print_header("9.1.11 Find Un-owned Files and Directories (Scored)")
check_empty(
    "df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -nouser -ls"
)

#
print_header("9.1.12 Find Un-grouped Files and Directories (Scored)")
check_empty(
    "df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -nogroup -ls"
)

#
print_header("9.1.13 Find SUID System Executables (Not Scored)")
print_warning("Check manually for invalid SUID permissions.")
view_output(
    "df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type f -perm -4000 -print"
)

#
print_header("9.1.14 Find SGID System Executables (Not Scored)")
print_warning("Check manually for invalid SGID permissions.")
view_output(
    "df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type f -perm -2000 -print"
)

#
print_header("9.2 Review User and Group Settings")

#
print_header("9.2.1 Ensure Password Fields are Not Empty (Scored)")
check_empty("""/bin/cat /etc/shadow | /bin/awk -F: '($2 == "" ) { print $1 " does not have apassword "}'""")

#
print_header('9.2.2 Verify No Legacy "+" Entries Exist in /etc/passwd File (Scored)')
check_empty("/bin/grep '^+:' /etc/passwd")

#
print_header('9.2.3 Verify No Legacy "+" Entries Exist in /etc/shadow File (Scored)')
check_empty(" /bin/grep '^+:' /etc/shadow")

#
print_header('9.2.4 Verify No Legacy "+" Entries Exist in /etc/group File (Scored)')
check_empty(" /bin/grep '^+:' /etc/group")

#
print_header("9.2.5 Verify No UID 0 Accounts Exist Other Than root (Scored)")
check_equal(
    "/bin/cat /etc/passwd | /bin/awk -F: '($3 == 0) { print $1 }'",
    "root"
)

#
print_header("9.2.6 Ensure root PATH Integrity (Scored)")
check_empty("""
if [ "`echo $PATH | /bin/grep :: `" != "" ]; then
      echo "Empty Directory in PATH (::)"
fi
if [ "`echo $PATH | /bin/grep :$`"  != "" ]; then
      echo "Trailing : in PATH"
fi
p=`echo $PATH | /bin/sed -e 's/::/:/' -e 's/:$//' -e 's/:/ /g'` set -- $p
while [ "$1" != "" ]; do
    if [ "$1" = "." ]; then
        echo "PATH contains ."
        shift
        continue
    fi
    if [ -d $1 ]; then
        dirperm=`/bin/ls -ldH $1 | /bin/cut -f1 -d" "`
        if [ `echo $dirperm | /bin/cut -c6 ` != "-" ]; then
            echo "Group Write permission set on directory $1"
        fi
        if [ `echo $dirperm | /bin/cut -c9 ` != "-" ]; then
            echo "Other Write permission set on directory $1"
        fi

        dirown=`ls -ldH $1 | awk '{print $3}'`
        if [ "$dirown" != "root" ] ; then
            echo $1 is not owned by root
        fi
        else
            echo $1 is not a directory
        fi
        shift
done
""")

#
print_header("9.2.7 Check Permissions on User Home Directories (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    dirperm=`/bin/ls -ld $dir | /bin/cut -f1 -d" "`
    if [ `echo $dirperm | /bin/cut -c6 ` != "-" ]; then
        echo "Group Write permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c8 ` != "-" ]; then
        echo "Other Read permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c9 ` != "-" ]; then
        echo "Other Write permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c10 ` != "-" ]; then
        echo "Other Execute permission set on directory $dir"
    fi
done
""")

#
print_header("9.2.8 Check User Dot File Permissions (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.[A-Za-z0-9]*; do
        if [ ! -h "$file" -a -f "$file" ]; then
            fileperm=`/bin/ls -ld $file | /bin/cut -f1 -d" "`
            if [ `echo $fileperm | /bin/cut -c6 ` != "-" ]; then
                echo "Group Write permission set on file $file"
            fi
            if [ `echo $fileperm | /bin/cut -c9 ` != "-" ]; then
                echo "Other Write permission set on file $file"
            fi
        fi
    done
done
""")

#
print_header("9.2.9 Check Permissions on User .netrc Files (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.netrc; do
        if [ ! -h "$file" -a -f "$file" ]; then
            fileperm=`/bin/ls -ld $file | /bin/cut -f1 -d" "`
            if [ `echo $fileperm | /bin/cut -c5 ` != "-" ]
            then
                echo "Group Read set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c6 ` != "-" ]
            then
                  echo "Group Write set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c7 ` != "-" ]
            then
                  echo "Group Execute set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c8 ` != "-" ]
            then
                  echo "Other Read  set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c9 ` != "-" ]
            then
                  echo "Other Write set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c10 ` != "-" ]
            then
                  echo "Other Execute set on $file"
            fi
        fi
    done
done
""")

#
print_header("9.2.10 Check for Presence of User .rhosts Files (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.rhosts; do
        if [ ! -h "$file" -a -f "$file" ]; then
            echo ".rhosts file in $dir"
        fi
    done
done
""")

#
print_header("9.2.11 Check Groups in /etc/passwd (Scored)")
check_empty("""
while read x
do
    userid=`echo "$x" | cut -f1 -d':'`
    groupid=`echo "$x" | /bin/cut -f4 -d':'`
    found=0

    while read line
    do
        y=`echo $line | cut -f3 -d":"`
        if [ $y -eq $groupid ]
        then
            found=1
            break
        fi
    done < /etc/group

    if [ $found -eq 0 ]
    then
        echo "Groupid $groupid does not exist in /etc/group, but is used by $userid"
    fi
done < /etc/passwd
""")

#
print_header("9.2.12 Check That Users Are Assigned Home Directories (Scored)")
check_empty("""
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    if [  -z "$dir" ]
    then
        echo "User $user has no home directory."
    fi
done
""")

#
print_header("9.2.13 Check That Defined Home Directories Exist (Scored)")
check_empty("""
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    if [ -z "${dir}" ]; then
        echo "User $user has no home directory."
    elif [ ! -d $dir ]; then
        echo "User $user home directory ($dir) not found"
    fi
done
""")

#
print_header("9.2.14 Check User Home Directory Ownership (Scored)")
check_empty("""
defUsers="bin daemon adm lp sync shutdown halt mail uucp operator games gopher ftp nobody vcsa saslauth postfix sshd ntp mailnull smmsp dbus apache haldaemon dhcpd"
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    found=0
    for n in $defUsers
    do
        if [ "$user" = "$n" ]
        then
            found=1
            break
        fi
    done
    if [ $found -eq "0" ]
    then
        owner=`stat -c "%U" $dir`
        if [ "$owner" != "$user" ]
        then
            echo "Home directory $dir for $user owned by $owner"
        fi
    fi
done
""")

#
print_header("9.2.15 Check for Duplicate UIDs (Scored)")
check_empty("""
/bin/cat /etc/passwd | /bin/cut -f3 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    set - $x
    if [ $1 -gt 1 ]; then
        users=`/bin/gawk -F: '($3 == n) { print $1 }' n=$2 /etc/passwd | /usr/bin/xargs`
        echo "Duplicate UID ($2): ${users}"
    fi
done
""")

#
print_header("9.2.16 Check for Duplicate GIDs (Scored)")
check_empty("""
/bin/cat /etc/group | /bin/cut -f3 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    set - $x
    if [ $1 -gt 1 ]; then
        users=`/bin/gawk -F: '($3 == n) { print $1 }' n=$2 /etc/group | /usr/bin/xargs`
        echo "Duplicate GID ($2): ${users}"
    fi
done
""")

#
print_header("9.2.17 Check That Reserved UIDs Are Assigned to System Accounts (Scored)")
check_empty("""
defUsers=" glassfish root bin daemon adm lp sync shutdown halt mail uucp operator games gopher ftp nobody vcsa saslauth postfix sshd ntp mailnull smmsp dbus apache haldaemon dhcpd"
/bin/cat /etc/passwd | /bin/awk -F: '($3 < 500) { print $1" "$3 }' |\
while read user uid; do
    found=0
    for tUser in ${defUsers}
    do
        if [ ${user} = ${tUser} ]; then
            found=1
            break
        fi
    done
    if [ $found -eq 0 ]; then
        echo "User $user has a reserved UID ($uid)."
    fi
done
""")

#
print_header("9.2.18 Check for Duplicate User Names (Scored)")
check_empty("""
cat /etc/passwd | cut -f1 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    [ -z "${x}" ] && break
    set - $x
    if [ $1 -gt 1 ]; then
        uids=`/bin/gawk -F: '($1 == n) { print $3 }' n=$2 /etc/passwd | xargs`
        echo "Duplicate User Name ($2): ${uids}"
    fi
done
""")

#
print_header("9.2.19 Check for Duplicate Group Names (Scored)")
check_empty("""
cat /etc/group | cut -f1 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    [ -z "${x}" ] && break
    set - $x
    if [ $1 -gt 1 ]; then
        gids=`/bin/gawk -F: '($1 == n) { print $3 }' n=$2 /etc/group | xargs`
        echo "Duplicate Group Name ($2): ${gids}"
    fi
done
""")

#
print_header("9.2.20 Check for Presence of User .netrc Files (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/awk -F: '{ print $6 }'`; do
    for file in $dir/.netrc; do
        if [ -f "$file" ]; then
            echo "File shouldn't exist, $file"
        fi
    done
done
""")

#
print_header("9.2.21 Check for Presence of User .forward Files (Scored)")
check_empty("""
for dir in `/bin/cat /etc/passwd | /bin/awk -F: '{ print $6 }'`; do
    for file in $dir/.forward; do
        if [ -f "$file" ]; then
            echo "File shouldn't exist, $file"
        fi
    done
done
""")
