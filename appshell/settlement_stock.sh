#!/bin/sh

echo "starting sync_dump_csvs..."
python ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs.py -conf ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs_stock.json
if [ $? != 0 ]; then
        echo "sync_dump_csvs stock error..."
        exit 1
fi

echo "starting prepare_settle_stock..."
python ${SIM_PLATFORM_HOME}/settlement/prepare_settle_stock.py
if [ $? != 0 ]; then
        echo "prepare_settle_stock error..."
        exit 1
fi

echo "starting snap_settle_data stock..."
python ${SIM_PLATFORM_HOME}/settlement/snap_settle_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_settle_data_stock.json
if [ $? != 0 ]; then
        echo "snap_settle_data stock error..."
        exit 1
fi

echo "starting snap_settle_data etf..."
python ${SIM_PLATFORM_HOME}/settlement/snap_settle_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_settle_data_etf.json
if [ $? != 0 ]; then
        echo "snap_settle_data etf error..."
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

echo "starting settle_etf..."
python ${SIM_PLATFORM_HOME}/settlement/settle_etf.py
if [ $? != 0 ]; then
        echo "settle_etf error..."
        exit 1
fi

echo "starting publish_stock_broker..."
python ${SIM_PLATFORM_HOME}/settlement/publish_stock_broker.py
if [ $? != 0 ]; then
        echo "publish_stock_broker error..."
        exit 1
fi


echo "starting publish_etf_broker..."
python ${SIM_PLATFORM_HOME}/settlement/publish_etf_broker.py
if [ $? != 0 ]; then
        echo "publish_etf_broker error..."
        exit 1
fi

echo "starting publish_stock_exchange..."
python ${SIM_PLATFORM_HOME}/settlement/publish_stock_exchange.py
if [ $? != 0 ]; then
        echo "publish_stock_exchange error..."
        exit 1
fi

echo "starting sync_activity_rankable_investor..."
python ${SIM_PLATFORM_HOME}/account/sync_activity_rankable_investor.py

echo "starting snap_initial_data stock..."
python ${SIM_PLATFORM_HOME}/settlement/snap_initial_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_initial_data_stock.json
if [ $? != 0 ]; then
        echo "snap_initial_data stock error..."
        exit 1
fi

echo "starting snap_initial_data etf..."
python ${SIM_PLATFORM_HOME}/settlement/snap_initial_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_initial_data_etf.json
if [ $? != 0 ]; then
        echo "snap_initial_data etf error..."
        exit 1
fi
