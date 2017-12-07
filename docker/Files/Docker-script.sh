#!/bin/bash 
chown -R www-data /Sites/online_test  
chmod -R 644 /Sites/online_test
chmod -R +X /Sites
/usr/sbin/apache2ctl -D FOREGROUND
