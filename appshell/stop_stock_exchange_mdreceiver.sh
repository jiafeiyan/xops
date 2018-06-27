#!/bin/sh
echo "starting stop_stock_exchange_mdreceiver..."
python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf ${SIM_PLATFORM_HOME}/appshell/stop_stock_exchange_mdreceiver.json
