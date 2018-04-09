#!/bin/sh

echo `python ${SIM_PLATFORM_HOME}/appshell/get_lasttradingday.py -conf ${SIM_PLATFORM_HOME}/appshell/get_lasttradingday_stock.json | tail -1`
