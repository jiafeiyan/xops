#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} crontab_tinit_stock.sh start..." | tee -a crontab.log

# 判断是否交易日
trading_day=`sh ${SIM_PLATFORM_HOME}/appshell/get_stock_tradingday.sh`

if [ "${trading_day}" != "${now_date}" ]; then
    echo "当前日期[${now_date}]非当前交易日[${trading_day}]..." | tee -a crontab.log
    exit 1
fi

# 1) shutdown stock broker
echo "start stop_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_broker.sh >> crontab.log

# 2) shutdown stock exchange
echo "start stop_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_exchange.sh >> crontab.log

# 3) sync_stock_broker_csvs.py
echo "start sync_stock_broker_csvs.py ... "
python ${SIM_PLATFORM_HOME}/settlement/sync_stock_broker_csvs.py >> crontab.log

# 4) settle_stock_userpwd.py
echo "start settle_stock_userpwd.py ... "
python ${SIM_PLATFORM_HOME}/settlement/settle_stock_userpwd.py >> crontab.log

# 5) toSyncAll.sh
echo "start toSyncAll.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/toSyncAll.sh >> crontab.log

# 6) stock_csv_all.sh
echo "start stock_csv_all ... "
sh ${SIM_PLATFORM_HOME}/appshell/stock_csv_all.sh >> crontab.log

# 7) tinit.sh
echo "start tinit.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/tinit.sh >> crontab.log

# 8) start stock exchange
echo "start start_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_exchange.sh >> crontab.log

# 9) start stock broker
echo "start start_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_broker.sh >> crontab.log


echo "${now_date} crontab_tinit_stock.sh finished..." | tee -a crontab.log