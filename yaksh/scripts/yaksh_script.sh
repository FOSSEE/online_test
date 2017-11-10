#!/bin/bash
# Basic script to install pip packages and run the yaksh code server command

chown -R nobody output
chmod -R a+rwX output
chmod -R a+rX data yaksh
chmod -R o-w data yaksh
echo "** Installing python dependencies **"
pip3 install -r ./requirements-codeserver.txt
echo "** Running code server **"
/usr/bin/sudo -su nobody python3 -m yaksh.code_server
