#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_close_future.sh start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/get_future_tradingday.sh`

if [ "${trading_day}" != "${now_date}" ]; then
    echo "当前日期[${now_date}]非当前交易日[${trading_day}]..." | tee -a crontab.log
#    exit 1
fi

# settlement_stock.sh
sh ${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/future/close_future_exchange.sh >> crontab.log

echo "${now_date} crontab_close_future.sh finished..." | tee -a crontab.log
