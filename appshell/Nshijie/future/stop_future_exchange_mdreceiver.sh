#!/bin/sh
echo "starting stop_future_exchange_mdreceiver..."
python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/stop_future_exchange_mdreceiver.json
