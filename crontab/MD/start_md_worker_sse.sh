#!/bin/sh
rm ./log/md_worker_sse.log
nohup python marketdata/md_worker.py -conf marketdata/md_worker_sse.json > ./log/md_worker_sse.log 2>&1 &
