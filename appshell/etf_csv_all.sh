#!/bin/sh

echo "starting exchange_stock_csv..."
python ${SIM_PLATFORM_HOME}/tinit/exchange_stock_csv.py

echo "starting broker_etf_csv..."
python ${SIM_PLATFORM_HOME}/tinit/broker_etf_csv.py