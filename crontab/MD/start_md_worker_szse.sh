#!/bin/sh
rm ./log/md_worker_szse.log
nohup python marketdata/md_worker.py -conf marketdata/md_worker_szse.json > ./log/md_worker_szse.log 2>&1 &
