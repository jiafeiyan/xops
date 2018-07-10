#!/bin/sh

echo `python ${SIM_PLATFORM_HOME}/appshell/get_tradingday.py | tail -1`
