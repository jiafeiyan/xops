#!/bin/sh
echo "starting load_ctp_info..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/future/get_future_tradingday.sh`

echo "current_trading_day="${current_trading_day}

mkdir ${HOME}/sim_data/${current_trading_day}

cd ${SIM_PLATFORM_HOME}/tools/ctploader
mkdir ${current_trading_day}

./ctploader 1 ${current_trading_day}

cp -f ${current_trading_day}/* ${HOME}/sim_data/${current_trading_day}
