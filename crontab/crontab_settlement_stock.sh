#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_settlement_stock start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/get_stock_tradingday.sh`

if [ "${trading_day}" != "${now_date}" ]; then
    echo "${now_date}属于非交易日..." | tee -a crontab.log
    exit 1
fi

# settlement_stock.sh
sh ${SIM_PLATFORM_HOME}/appshell/settlement_stock.sh >> crontab.log

echo "${now_date} crontab_settlement_stock finished..." | tee -a crontab.log