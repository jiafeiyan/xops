# -*- coding: UTF-8 -*-

import rsh_tool

config = {"host": "192.188.188.101", "user": "root", "password": "111111"}

rsh = rsh_tool.rsh(config)

rsh.trans_connect()
rsh.scp("F:\\platform\\20171228jy", "/root/temp")
rsh.trans_disconnect()

rsh.ssh_connect()
rsh.execute("tar -czvf mydbf.tar.gz /root/temp")
rsh.ssh_disconnect()