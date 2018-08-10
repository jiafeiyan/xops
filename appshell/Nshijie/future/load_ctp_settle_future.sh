#!/bin/sh
echo "starting load_ctp_settle_future..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/get_future_tradingday.sh`

echo "current_trading_day="${current_trading_day}

cd ${SIM_PLATFORM_HOME}/tools/ctploader

./ctploader 1 ${current_trading_day}

cp -f ${current_trading_day}/future_depthmarketdata.csv ${SIM_PLATFORM_HOME}/settlement_data/0002/1
cp -f ${current_trading_day}/future_depthmarketdata.csv ${HOME}/sim_data/${current_trading_day}/future_depthmarketdata_settle.csv
