#!/bin/sh
# check Trade.csv
fileSize=`ls -l | grep -w 'Trade.csv' | awk -F " " '{ print $5}'`
echo $fileSize

while true
do
	if [ "$fileSize" != "0" ]; then
		fileSize=`ls -l | grep -w 'Trade.csv' | awk -F " " '{ print $5}'`
		sleep 60
		temp=`ls -l | grep -w 'Trade.csv' | awk -F " " '{ print $5}'`
		if [ $fileSize == $temp ]; then
			break
		fi
	fi
	sleep 1
done

echo check Trade.csv end