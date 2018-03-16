#!/bin/sh

echo "starting sync_dump_csvs..."
python ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs.py
if [ $? != 0 ]; then
        echo "sync_dump_csvs error..."
        exit 1
fi

echo "starting prepare_settle_stock..."
python ${SIM_PLATFORM_HOME}/settlement/prepare_settle_stock.py
if [ $? != 0 ]; then
        echo "prepare_settle_stock error..."
        exit 1
fi

echo "starting snap_settle_data..."
python ${SIM_PLATFORM_HOME}/settlement/snap_settle_data.py
if [ $? != 0 ]; then
        echo "snap_settle_data error..."
        exit 1
fi

echo "starting settle_stock..."
python ${SIM_PLATFORM_HOME}/settlement/settle_stock.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_stock_sse.json
if [ $? != 0 ]; then
        echo "settle_stock sse error..."
        exit 1
fi
python ${SIM_PLATFORM_HOME}/settlement/settle_stock.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_stock_szse.json
if [ $? != 0 ]; then
        echo "settle_stock szse error..."
        exit 1
fi

echo "starting publish_stock_broker..."
python ${SIM_PLATFORM_HOME}/settlement/publish_stock_broker.py
if [ $? != 0 ]; then
        echo "publish_stock_broker error..."
        exit 1
fi

echo "starting publish_stock_exchange..."
python ${SIM_PLATFORM_HOME}/settlement/publish_stock_exchange.py
if [ $? != 0 ]; then
        echo "publish_stock_exchange error..."
        exit 1
fi

echo "starting settle_activity..."
python ${SIM_PLATFORM_HOME}/settlement/settle_activity.py
if [ $? != 0 ]; then
        echo "settle_activity error..."
        exit 1
fi

echo "starting snap_activity_data..."
python ${SIM_PLATFORM_HOME}/settlement/snap_activity_data.py
if [ $? != 0 ]; then
        echo "snap_activity_data error..."
        exit 1
fi

echo "starting snap_initial_data..."
python ${SIM_PLATFORM_HOME}/settlement/snap_initial_data.py
if [ $? != 0 ]; then
        echo "snap_initial_data error..."
        exit 1
fi
