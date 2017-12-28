#!/bin/bash
chown -R nobody /Sites/online_test/yaksh_data
chmod -R a+rwX yaksh_data/output
chmod -R a+rX yaksh_data/data
chmod -R o-w yaksh_data/data
/usr/bin/sudo -su nobody python3 -m yaksh.code_server
