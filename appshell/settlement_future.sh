#!/bin/sh

echo "starting sync_dump_csvs..."
python ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs.py
if [ $? != 0 ]; then
        echo "sync_dump_csvs error..."
        exit 1
fi

echo "starting prepare_settle_futures..."
python ${SIM_PLATFORM_HOME}/settlement/prepare_settle_futures.py
if [ $? != 0 ]; then
        echo "prepare_settle_futures error..."
        exit 1
fi

echo "starting settle_future..."
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py
if [ $? != 0 ]; then
        echo "settle_future error..."
        exit 1
fi

echo "starting publish_future_broker..."
python ${SIM_PLATFORM_HOME}/settlement/publish_future_broker.py
if [ $? != 0 ]; then
        echo "publish_future_broker error..."
        exit 1
fi

echo "starting publish_future_exchange..."
python ${SIM_PLATFORM_HOME}/settlement/publish_future_exchange.py
if [ $? != 0 ]; then
        echo "publish_future_exchange error..."
        exit 1
fi
