#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/${SIM_RELEASE}/stock/get_stock_tradingday.sh`

# settlement_stock.sh
sh ${SIM_PLATFORM_HOME}/appshell/settlement_activity.sh >> crontab.log

echo "${now_date} crontab_settlement_activity finished..." | tee -a crontab.log