#!/bin/bash 
chown -R apache /Sites/online_test
chown -R apache /Sites/online_test/yaksh
chown -R nobody /Sites/online_test/yaksh_data
chmod -R 664 /Sites/online_test
chmod -R +X /Sites
/usr/sbin/httpd -D FOREGROUND
