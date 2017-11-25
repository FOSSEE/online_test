#!/bin/bash
chown -R nobody /Sites/online_test
chmod -R a+rwX yaksh_data/output
chmod -R a+rX yaksh_data/data yaksh_data/yaksh
chmod -R o-w yaksh_data/data yaksh
chmod -R +X /Sites/online_test/
/usr/bin/sudo -su nobody python3 -m yaksh.code_server
