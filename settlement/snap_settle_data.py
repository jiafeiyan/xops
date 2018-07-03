# -*- coding: UTF-8 -*-

import json

from utils import log, mysql, Configuration, parse_conf_args, process_assert


def snap_data(context, conf):
    result_code = 0
    logger = log.get_logger(category="SnapSettleData")

    broker_system_id = conf.get("brokerSystemId")

    logger.info("[snap settle data %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT 
                              DISTINCT t1.tradingday 
                            FROM
                              siminfo.t_tradesystemtradingday t1,
                              siminfo.t_tradesystemsettlementgroup t2,
                              siminfo.t_brokersystemsettlementgroup t3 
                            WHERE t1.tradesystemid = t2.tradesystemid 
                              AND t2.settlementgroupid = t3.settlementgroupid 
                              AND t3.brokersystemid = %s"""
        cursor.execute(sql, (broker_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))

        logger.info("[snap order]......")
        sql = """INSERT INTO snap.t_s_order(TradingDay,SettlementGroupID,SettlementID,OrderSysID,ParticipantID,ClientID,UserID,InstrumentID,OrderPriceType,Direction,CombOffsetFlag,CombHedgeFlag,LimitPrice,VolumeTotalOriginal,TimeCondition,GTDDate,VolumeCondition,MinVolume,ContingentCondition,StopPrice,ForceCloseReason,OrderLocalID,IsAutoSuspend,OrderSource,OrderStatus,OrderType,VolumeTraded,VolumeTotal,InsertDate,InsertTime,ActiveTime,SuspendTime,UpdateTime,CancelTime,ActiveUserID,Priority,TimeSortID,ClearingPartID,BusinessUnit)
                            SELECT TradingDay,SettlementGroupID,SettlementID,OrderSysID,ParticipantID,ClientID,UserID,InstrumentID,OrderPriceType,Direction,CombOffsetFlag,CombHedgeFlag,LimitPrice,VolumeTotalOriginal,TimeCondition,GTDDate,VolumeCondition,MinVolume,ContingentCondition,StopPrice,ForceCloseReason,OrderLocalID,IsAutoSuspend,OrderSource,OrderStatus,OrderType,VolumeTraded,VolumeTotal,InsertDate,InsertTime,ActiveTime,SuspendTime,UpdateTime,CancelTime,ActiveUserID,Priority,TimeSortID,ClearingPartID,BusinessUnit
                            FROM dbclear.t_order WHERE tradingday = %s AND settlementgroupid in (SELECT settlementgroupid FROM siminfo.t_brokersystemsettlementgroup where brokersystemid = %s)"""
        cursor.execute(sql, (current_trading_day, broker_system_id,))
        logger.info("[snap trade]......")
        sql = """INSERT INTO snap.t_s_trade(TradingDay,SettlementGroupID,SettlementID,TradeID,Direction,OrderSysID,ParticipantID,ClientID,TradingRole,AccountID,InstrumentID,OffsetFlag,HedgeFlag,Price,Volume,TradeTime,TradeType,PriceSource,UserID,OrderLocalID,ClearingPartID,BusinessUnit)
                            SELECT TradingDay,SettlementGroupID,SettlementID,TradeID,Direction,OrderSysID,ParticipantID,ClientID,TradingRole,AccountID,InstrumentID,OffsetFlag,HedgeFlag,Price,Volume,TradeTime,TradeType,PriceSource,UserID,OrderLocalID,ClearingPartID,BusinessUnit
                            FROM dbclear.t_trade WHERE tradingday = %s AND settlementgroupid in (SELECT settlementgroupid FROM siminfo.t_brokersystemsettlementgroup where brokersystemid = %s)"""
        cursor.execute(sql, (current_trading_day, broker_system_id,))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[snap settle data] Error: %s" % (e))
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[snap settle data] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(snap_data(context, conf))


if __name__ == "__main__":
    main()