#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_tinit_future.sh start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/get_future_tradingday.sh`
last_trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/get_future_lasttradingday.sh`

if [ "${last_trading_day}" != "${now_date}" ]; then
    echo "当前日期[${now_date}]非当前交易日[${trading_day}]前一交易日[${last_trading_day}]..." | tee -a crontab.log
    exit 1
fi

# 1) shutdown future broker
echo "start stop_future_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_future_broker.sh >> crontab.log

# 2) shutdown future exchange
echo "start stop_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_future_exchange.sh >> crontab.log

# 3) load ctp info
echo "start load_ctp_info.sh ..."
sh ${SIM_PLATFORM_HOME}/appshell/load_ctp_info.sh >> crontab.log

# 4) data trans
echo "start trans_futureinfo.sh ..."
sh ${SIM_PLATFORM_HOME}/appshell/trans_futureinfo.sh >> crontab.log
# 3) sync_stock_broker_csvs.py
#echo "start sync_stock_broker_csvs.py ... "
#python ${SIM_PLATFORM_HOME}/settlement/sync_stock_broker_csvs.py >> crontab.log
#
## 4) settle_stock_userpwd.py
#echo "start settle_stock_userpwd.py ... "
#python ${SIM_PLATFORM_HOME}/settlement/settle_stock_userpwd.py >> crontab.log

# 5) toSyncAll.sh
echo "start toSyncAll.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/toSyncAll_future.sh >> crontab.log

# 6) future_csv_all.sh
echo "start future_csv_all ... "
sh ${SIM_PLATFORM_HOME}/appshell/future_csv_all.sh >> crontab.log

# 7) tinit.sh
echo "start tinit.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/tinit_future.sh >> crontab.log

# 8) start future exchange
echo "start start_future_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_future_exchange.sh >> crontab.log

# 9) start future broker
echo "start start_future_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_future_broker.sh >> crontab.log

# 10) sleep 2 minutes
sleep 120

# 11) fire tinit
echo "start fire_tinit.sh ..."
sh ${SIM_PLATFORM_HOME}/appshell/fire_tinit.sh >> crontab.log

echo "${now_date} crontab_tinit_future.sh finished..." | tee -a crontab.log
