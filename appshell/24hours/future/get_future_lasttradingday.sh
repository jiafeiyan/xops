#!/bin/sh

echo `python ${SIM_PLATFORM_HOME}/appshell/get_lasttradingday.py -conf appshell/get_lasttradingday_future.json | tail -1`
