chown root:public /opt
chmod -R u=srwx,g=srwx /opt

chown -R root:public /opt/backup
chown -R root:public /opt/data

chown -R root:management /opt/data/users/Document/0\ Management
chown -R root:management /opt/data/users/Document/4\ Admin

chcon -t samba_share_t /opt/backup
chcon -t samba_share_t /opt/data

# Setup rssh and sftp

cd /opt/data/users/
rm -rf /opt/data/users/usr
rm -rf /opt/data/users/lib
rm -rf /opt/data/users/etc
rm -rf /opt/data/users/dev

mkdir -p /opt/data/users/{dev,etc,lib,usr}
mkdir -p /opt/data/users/usr/bin
mkdir -p /opt/data/users/usr/libexec/openssh/

mknod -m 666 /opt/data/users/dev/null c 1 3

cd /opt/data/users/etc
cp /etc/ld.so.cache .
cp /etc/ld.so.conf .
cp /etc/nsswitch.conf .
cp /etc/passwd .
cp /etc/group .
cp /etc/hosts .
cp /etc/resolv.conf .


cd /opt/data/users/usr/bin
cp /usr/bin/scp .
cp /usr/bin/rssh .
cp /usr/bin/sftp .
cd /opt/data/users/usr/libexec/openssh/
cp /usr/libexec/openssh/sftp-server .


l2chroot /usr/bin/scp
l2chroot /usr/bin/rssh
l2chroot /usr/bin/sftp
l2chroot /usr/libexec/openssh/sftp-server

/etc/init.d/sshd restart
/etc/init.d/syslog restart
