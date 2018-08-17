#!/bin/sh
rm nohup.out
nohup python marketdata/md_calc.py -conf marketdata/md_calc_sse.json &
#nohup python marketdata/md_calc.py -conf marketdata/md_calc_sse.json &
