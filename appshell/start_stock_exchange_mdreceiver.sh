#!/bin/sh
echo "starting start_stock_exchange_mdreceiver..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/get_stock_tradingday.sh`
add_ons="{\"parameters\":{\"tradingday\":\"${current_trading_day}\"}}"

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf ${SIM_PLATFORM_HOME}/appshell/start_stock_exchange_mdreceiver.json -ads=${add_ons}
