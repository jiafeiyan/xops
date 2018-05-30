#!/bin/sh
echo "starting load_ctp_settle_future..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/get_future_tradingday.sh`

echo "current_trading_day="${current_trading_day}

cd ${SIM_PLATFORM_HOME}/tools/ctploader

./ctploader 1 ${current_trading_day}

cp -f ${current_trading_day}/future_depthmarketdata.csv ${HOME}/settlement_data/0002/1
