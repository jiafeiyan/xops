#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_restart_future_exchange_mdreceiver.sh start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/future/get_future_tradingday.sh`

if [ "${trading_day}" != "${now_date}" ]; then
    echo "当前日期[${now_date}]非当前交易日[${trading_day}]..." | tee -a crontab.log
#    exit 1
fi

# 1) shutdown future exchange mdreceiver 
echo "start stop_future_exchange_mdreceiver.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/future/stop_future_exchange_mdreceiver.sh >> crontab.log

# 2) start future exchange mdreceiver
echo "start start_future_exchange_mdreceiver.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/future/start_future_exchange_mdreceiver.sh >> crontab.log

echo "${now_date} crontab_restart_future_exchange_mdreceiver.sh finished..." | tee -a crontab.log
