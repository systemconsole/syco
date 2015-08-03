#!/usr/bin/env python
'''
Setup proxy function

'''

from general import x
import app
from scopen import scOpen


def install_proxy_setup():
    if not os.path.exists('/etc/profile.d/proxy.sh'):
        x("cp %shardening/proxy.sh /etc/profile.d" % app.SYCO_VAR_PATH)
        x("chmod 644 /etc/profile.d/proxy.sh")
        #Pass proxy variable when running sudo
        proxenv='Defaults env_keep +="http_proxy"'
        x("echo "+proxenv+" >> /etc/sudoers")
