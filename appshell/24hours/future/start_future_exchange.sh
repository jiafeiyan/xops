#!/bin/sh
echo "starting start_future_exchange..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/get_future_tradingday.sh`
add_ons="{\"parameters\":{\"tradingday\":\"${current_trading_day}\"}}"

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/start_future_exchange.json -ads=${add_ons}