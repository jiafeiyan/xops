#!/bin/sh
rm ./log/md_calc_szse*
nohup python marketdata/md_calc.py -conf marketdata/md_calc_szse.json &
nohup python marketdata/md_calc.py -conf marketdata/md_calc_szse.json &
