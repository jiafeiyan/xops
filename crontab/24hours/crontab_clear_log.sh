#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} clear_log start..." | tee -a crontab.log

# clear_log.sh
sh ${SIM_PLATFORM_HOME}/appshell/clear_log.sh >> crontab.log

echo "${now_date} clear_log finished..." | tee -a crontab.log
