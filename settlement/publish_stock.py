# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args


def publish_stock(context, conf):
    logger = log.get_logger(category="PublishStock")

    settlement_group_id = conf.get("settlementGroupId")
    settlement_id = conf.get("settlementId")

    logger.info("[publish stock %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT t1.tradingday FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2 WHERE t1.tradesystemid = t2.tradesystemid and t2.settlementgroupid = %s"""
        cursor.execute(sql, (settlement_group_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))

        logger.info("[get next trading day]......")
        sql = """SELECT DAY FROM siminfo.t_TradingCalendar t WHERE t.day > %s AND t.tra = '1' ORDER BY DAY LIMIT 1"""
        cursor.execute(sql, (current_trading_day,))
        row = cursor.fetchone()

        next_trading_day = str(row[0])
        logger.info("[get next trading day] next_trading_day = %s" % (next_trading_day))

        # 检查结算状态
        logger.info("[check settlement status]......")
        sql = """SELECT 
                      t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.settlementstatus
                    FROM
                      dbclear.t_settlement t1
                    WHERE t1.tradingday = %s
                      AND t1.settlementgroupid = %s
                      AND t1.settlementid = %s for update"""
        cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        row = cursor.fetchone()

        if row is None:
            logger.error("[publish stock] Error: There is no data for %s-%s." % (settlement_group_id, settlement_id))
        elif row[3] == '0':
            logger.error("[publish stock] Error: Settlement for %s-%s has not done." % (settlement_group_id, settlement_id))
        elif row[3] == '2':
            logger.error("[publish stock] Error: Settlement for %s-%s has been published." % (settlement_group_id, settlement_id))
        else:
            # 更新客户持仓
            logger.info("[update client position]......")
            sql = """DELETE FROM siminfo.t_clientposition WHERE settlementgroupid = %s"""
            cursor.execute(sql, (settlement_group_id,))
            sql = """INSERT INTO siminfo.t_clientposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID)
                                SELECT %s,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,Position,0,0,0,LongFrozen,ShortFrozen,0,0,0,PositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID
                                FROM dbclear.t_clientposition t WHERE t .tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
            cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

            # 更新会员持仓
            logger.info("[update part position]......")
            sql = """DELETE FROM siminfo.t_partposition WHERE settlementgroupid = %s"""
            cursor.execute(sql, (settlement_group_id,))
            sql = """INSERT INTO siminfo.t_partposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,InstrumentID,ParticipantID,TradingRole)
                                SELECT %s,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,Position,0,0,0,LongFrozen,ShortFrozen,InstrumentID,ParticipantID,TradingRole
                                FROM dbclear.t_partposition t WHERE t .tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
            cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

            # 更新行情数据
            logger.info("[update marketdata]......")
            sql = """DELETE FROM siminfo.t_marketdata WHERE settlementgroupid = %s"""
            cursor.execute(sql, (settlement_group_id,))
            sql = """INSERT INTO siminfo.t_marketdata(TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,PreClosePrice,PreOpenInterest,OpenPrice,HighestPrice,LowestPrice,Volume,Turnover,OpenInterest,ClosePrice,SettlementPrice,UpperLimitPrice,LowerLimitPrice,PreDelta,CurrDelta,UpdateTime,UpdateMillisec,InstrumentID)
                                SELECT %s,SettlementGroupID,NULL,PreSettlementPrice,PreClosePrice,PreOpenInterest,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,UpdateTime,UpdateMillisec,InstrumentID
                                FROM dbclear.t_marketdata t WHERE t .tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
            cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

            # 更新客户资金
            logger.info("[update client fund]......")
            sql = """DELETE FROM siminfo.t_clientfund WHERE settlementgroupid = %s"""
            cursor.execute(sql, (settlement_group_id,))
            sql = """INSERT INTO siminfo.t_clientfund(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,Available,TransFee,DelivFee,PositionMargin,Profit,StockValue)
                                            SELECT %s,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,Available,TransFee,DelivFee,PositionMargin,Profit,StockValue
                                            FROM dbclear.t_clientfund t WHERE t .tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s
                                            AND (t.available != 0 OR t.transfee != 0 OR t.delivfee != 0 OR t.positionmargin != 0 OR t.profit != 0 OR t.stockvalue != 0)"""
            cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

            # 更新投资者资金
            logger.info("[update investor fund]......")
            sql = """UPDATE siminfo.t_investorfund t1,(
                                SELECT t3.brokersystemid, t1.investorid, t2.available, t2.transfee, t2.stockvalue FROM siminfo.t_investorclient t1, dbclear.t_clientfund t2, siminfo.t_brokersystemsettlementgroup t3
                                WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.settlementgroupid = t3.settlementgroupid AND t1.clientid = t2.clientid AND t2.tradingday = %s AND t1.settlementgroupid = %s AND t2.settlementid = %s) t2
                                SET t1.prebalance = t1.balance, t1.balance = t1.available + t2.available - t2.transfee, t1.available = t1.available + t2.available - t2.transfee, t1.fee = t2.transfee
                                WHERE t1.brokersystemid = t2.brokersystemid and t1.investorid = t2.investorid"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id, current_trading_day))

            # 更新结算状态
            logger.info("[update settlement status]......")
            sql = """UPDATE dbclear.t_settlement SET settlementstatus = '2' WHERE tradingday = %s AND settlementgroupid = %s AND settlementid = %s AND settlementstatus = '1'"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[publish stock] Error: %s" % (e))
    finally:
        mysql_conn.close()
    logger.info("[publish stock] end")


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    publish_stock(context, conf)


if __name__ == "__main__":
    main()