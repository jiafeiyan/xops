#!/bin/sh
echo "starting fire_tinit..."

current_trading_day=`${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/get_future_tradingday.sh`

echo "current_trading_day="${current_trading_day}

cd ${SIM_PLATFORM_HOME}/tools/tinitclient

./tinitclient ${current_trading_day}

