#!/bin/bash

function proxy() {
echo "Proxy username:"
read -e username
echo "password:"
read -es password
proxyhost=$(grep http.proxy.host /opt/syco/etc/general.cfg |cut -c18-32)
proxyport=$(grep http.proxy.port /opt/syco/etc/general.cfg |cut -c18-22)
export http_proxy="http://$username:$password@$proxyhost:$proxyport/"
}