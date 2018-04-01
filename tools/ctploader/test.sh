#!/bin/sh

export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH

while [ "1" = "1" ]
do
mv 20180330 20180330_`date +%Y%m%d%H%M%S`
mkdir 20180330
./ctploader 1 20180330

sleep 300
done
