#!/bin/sh
echo "starting szse_trade_worker.sh..."
python ${SIM_PLATFORM_HOME}/extrader/trader_worker.py -conf ${SIM_PLATFORM_HOME}/extrader/trader_worker_szse.json