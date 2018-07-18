#!/bin/sh
echo "starting check_future_file_close.sh..."

python ${SIM_PLATFORM_HOME}/appshell/service_shell.py -conf appshell/check_future_file_close.json
