#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

python ${SIM_PLATFORM_HOME}/account/gen_investor.py >> crontab.log
python ${SIM_PLATFORM_HOME}/account/sync_gen_investor.py >> crontab.log

echo "crontab_sync_mddepot.sh finished..." | tee -a crontab.log