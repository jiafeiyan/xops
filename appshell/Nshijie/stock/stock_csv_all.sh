#!/bin/sh

echo "starting exchange_stock_csv..."
python ${SIM_PLATFORM_HOME}/tinit/exchange_stock_csv.py

echo "starting broker_stock_csv..."
python ${SIM_PLATFORM_HOME}/tinit/broker_stock_csv.py

echo "starting broker_sse_csv..."
python ${SIM_PLATFORM_HOME}/tinit/broker_sse_csv.py

echo "starting broker_szse_csv..."
python ${SIM_PLATFORM_HOME}/tinit/broker_szse_csv.py