#!/bin/bash

function proxy() {
echo "Proxy username:"
read -e username
echo "password:"
read -es password
export http_proxy="http://$username:$password@${proxyhost}:${proxyport}/"
}