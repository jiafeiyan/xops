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