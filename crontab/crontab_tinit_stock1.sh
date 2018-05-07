#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

echo "start stop_etf_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_etf_broker.sh >> crontab.log

# 2) shutdown stock broker
echo "start stop_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_broker.sh >> crontab.log

# 3) shutdown stock exchange
echo "start stop_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/stop_stock_exchange.sh >> crontab.log

# 6) sync_etf_broker_csvs.py
echo "start sync_etf_broker_csvs.py ... "
python ${SIM_PLATFORM_HOME}/settlement/sync_etf_broker_csvs.py >> crontab.log

# 7) trans_etfinfo.sh
echo "start sync_etf_broker_csvs.py ... "
sh ${SIM_PLATFORM_HOME}/appshell/trans_etfinfo.sh >> crontab.log

# 8) toSyncAll.sh
echo "start toSyncAll.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/toSyncAll.sh >> crontab.log

# 9) stock_csv_all.sh
echo "start stock_csv_all ... "
sh ${SIM_PLATFORM_HOME}/appshell/stock_csv_all.sh >> crontab.log

# 10) etf_csv_all.sh
echo "start stock_csv_all ... "
sh ${SIM_PLATFORM_HOME}/appshell/etf_csv_all.sh >> crontab.log

# 11) tinit.sh
echo "start tinit.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/tinit.sh >> crontab.log

# 12) start stock exchange
echo "start start_stock_exchange.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_exchange.sh >> crontab.log

# 13) start stock broker
echo "start start_stock_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_stock_broker.sh >> crontab.log

# 14) start etf broker
echo "start start_etf_broker.sh ... "
sh ${SIM_PLATFORM_HOME}/appshell/start_etf_broker.sh >> crontab.log


echo "${now_date} crontab_tinit_stock.sh finished..." | tee -a crontab.log
