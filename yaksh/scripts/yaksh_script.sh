#!/bin/bash
# Basic script to install pip packages and run the yaksh code server command

mkdir /sites/
echo "** Copying online test directory **"
cp -r /src/online_test /sites/online_test
cd /sites/online_test
echo "** Unmounting online test volume **"
umount /src/online_test
echo "** Installing python dependencies **"
pip3 install -r /sites/online_test/requirements/requirements-codeserver.txt
echo "** Running code server **"
python3 -m yaksh.code_server
