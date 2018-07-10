#!/bin/sh

echo "starting exchange_future_csv..."
python ${SIM_PLATFORM_HOME}/tinit/exchange_future_csv.py

echo "starting broker_future_csv..."
python ${SIM_PLATFORM_HOME}/tinit/broker_future_csv.py
