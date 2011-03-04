System Console
==============
Customized scripts for installation of services/application on linux servers.

CLONING
ssh-keygen -t rsa
cat ~/.ssh/id_rsa.pub
# Insert the output into www.github.com.
git clone git@github.com:arlukin/syco.git

# Add private/customized scripts.
cd syco
mkdir usr
cd usr
git clone git@github.com:arlukin/syco-template.git

DOCUMENTATION
-------------

THE FLOW OF THE "syco remote-install"

* Download syco from git
* On fo-tp-vh01 "syco remote-install fo-tp-vh01"
** On fo-tp-vh01 "syco hardening"
** On fo-tp-vh01 "syco install-kvmhost"
** On fo-tp-vh01 "syco install-fo-tp-install"
** On fo-tp-vh01 "syco install-guests"
*** On fo-tp-vh01, install fp-tp-system1
*** On fo-tp-vh01, install fp-tp-gf
** On fo-tp-install "syco git-clone"
** On fo-tp-install "syco hardening"
** On fo-tp-install "syco install-cobbler"
** On fo-tp-install "syco remote-install"
*** Look for alive hosts defined in install.cfg
*** Run "syco remote-install xx" on the host alive.
*** Continue until "remote-install" has been executed on all servers. 

