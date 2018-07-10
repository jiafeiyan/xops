#!/bin/sh
echo "starting load_ctp_settle_future..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/get_future_tradingday.sh`

echo "current_trading_day="${current_trading_day}

cp -f ${HOME}/sim_data/${current_trading_day}/future_depthmarketdata.csv ${SIM_PLATFORM_HOME}/settlement_data/00102/1

