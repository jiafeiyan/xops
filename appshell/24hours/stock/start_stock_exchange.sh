#!/bin/sh
echo "starting start_stock_exchange..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/stock/get_stock_tradingday.sh`
add_ons="{\"parameters\":{\"tradingday\":\"${current_trading_day}\"}}"

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/start_stock_exchange.json -ads=${add_ons}