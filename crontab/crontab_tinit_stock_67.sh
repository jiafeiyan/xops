#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_tinit_stock.sh start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/get_stock_lasttradingday.sh`

echo "当前日期[${now_date}];当前交易日[${trading_day}]..." | tee -a crontab.log

# 1) shutdown etf broker
echo "start stop_etf_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_etf_broker.sh >> crontab.log

# 2) shutdown stock broker
echo "start stop_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_broker.sh >> crontab.log

# 3) shutdown stock exchange
echo "start stop_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_exchange.sh >> crontab.log

# 12) start stock exchange
echo "start start_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_exchange_67.sh >> crontab.log

# 13) start stock broker
echo "start start_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_broker.sh >> crontab.log

# 14) start etf broker
echo "start start_etf_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_etf_broker.sh >> crontab.log


echo "${now_date} crontab_tinit_stock.sh finished..." | tee -a crontab.log
