#!/bin/sh
source ${HOME}/.bash_profile
cd ${SIM_PLATFORM_HOME}/crontab

today=`date +%Y%m%d`

echo "${today} crontab_dump_mysql.sh start..." | tee -a crontab.log

mkdir -p ${HOME}/database_backup/${today}

/usr/local/mysql/bin/mysqldump -uroot -p111111 --databases siminfo sync dbclear snap simtrade > ${HOME}/database_backup/${today}/mysql.sql

tar -C ${HOME}/database_backup/${today} -czvf ${HOME}/database_backup/${today}/mysql.tar.gz mysql.sql

rm -f ${HOME}/database_backup/${today}/mysql.sql

echo "${today} crontab_dump_mysql.sh finished..." | tee -a crontab.log

