#!/bin/sh
echo "starting start_future_exchange_mdreceiver..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/future/get_future_tradingday.sh`
add_ons="{\"parameters\":{\"tradingday\":\"${current_trading_day}\"}}"

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/start_future_exchange_mdreceiver.json -ads=${add_ons}
