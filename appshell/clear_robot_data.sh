#!/bin/sh

trade_system_id=$1
settlement_id=$2

cd ${SIM_PLATFORM_HOME}/settlement_data/${trade_system_id}/${settlement_id}

mv ClientPosition.csv ClientPosition.csv.orig
mv PartPosition.csv PartPosition.csv.orig
mv Order.csv Order.csv.orig
mv Trade.csv Trade.csv.orig

grep -v "R0001" ClientPosition.csv.orig > ClientPosition.csv
grep -v "R0001" PartPosition.csv.orig > PartPosition.csv
grep -v "R0001" Order.csv.orig > Order.csv
grep -v "R0001" Trade.csv.orig > Trade.csv

