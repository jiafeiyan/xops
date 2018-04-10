#!/bin/sh

echo "starting sync_dump_csvs..."
python ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs.py -conf ${SIM_PLATFORM_HOME}/settlement/sync_dump_csvs_future.json
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

echo "starting snap_settle_data..."
python ${SIM_PLATFORM_HOME}/settlement/snap_settle_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_settle_data_future.json
if [ $? != 0 ]; then
        echo "snap_settle_data future error..."
        exit 1
fi

echo "starting settle_future..."
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_future_shfe.json
if [ $? != 0 ]; then
        echo "settle_future shfe error..."
        exit 1
fi
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_future_dce.json
if [ $? != 0 ]; then
        echo "settle_future dce error..."
        exit 1
fi
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_future_czce.json
if [ $? != 0 ]; then
        echo "settle_future czce error..."
        exit
fi
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_future_cffex.json
if [ $? != 0 ]; then
        echo "settle_future cffex error..."
        exit 1
fi
python ${SIM_PLATFORM_HOME}/settlement/settle_future.py -conf ${SIM_PLATFORM_HOME}/settlement/settle_future_ine.json
if [ $? != 0 ]; then
        echo "settle_future ine error..."
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

echo "starting snap_initial_data..."
python ${SIM_PLATFORM_HOME}/settlement/snap_initial_data.py -conf ${SIM_PLATFORM_HOME}/settlement/snap_initial_data_future.json
if [ $? != 0 ]; then
        echo "snap_initial_data future error..."
        exit 1
fi
