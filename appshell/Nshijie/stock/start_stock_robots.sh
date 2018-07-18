#!/bin/sh
echo "starting start_stock_robots..."

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/start_stock_robots.json
