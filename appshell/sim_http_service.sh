#!/bin/sh
echo "starting sim_http_serv..."
nohup python ${SIM_PLATFORM_HOME}/account/sim_http_serv.py >> ${SIM_PLATFORM_HOME}/account/sim_http_serv.log 2>&1 &