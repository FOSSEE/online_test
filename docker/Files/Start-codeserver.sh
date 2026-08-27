#!/bin/bash
#mkdir  /Sites/online_test/yaksh_data && mkdir -p /Sites/online_test/yaksh_data/output /Sites/online_test/yaksh_data/data
chown -R nobody:nobody /Sites/online_test/yaksh_data
chmod -R a+rwX /Sites/online_test/yaksh_data/output
chmod -R a+rX /Sites/online_test/yaksh_data/data
chmod -R o-w /Sites/online_test/yaksh_data/data
/usr/bin/sudo -su nobody python3 -m yaksh.code_server
