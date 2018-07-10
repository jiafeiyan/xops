#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

# 获取系统时间
now_date=`date +%Y%m%d`

echo "${now_date} archive_csv start..." | tee -a crontab.log

# archive_csv.sh
sh ${SIM_PLATFORM_HOME}/appshell/archive_csv.sh >> crontab.log

echo "${now_date} archive_csv finished..." | tee -a crontab.log
