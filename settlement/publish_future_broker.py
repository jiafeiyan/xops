# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def publish_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="PublishFutureBroker")

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')

    broker_system_id = conf.get("brokerSystemId")

    logger.info("[publish future broker %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")

        sql = """SELECT DISTINCT t1.tradingday, t1.lasttradingday
                   FROM siminfo.t_tradesystemtradingday t1,
                        siminfo.t_tradesystemsettlementgroup t2,
                        siminfo.t_brokersystemsettlementgroup t3 
                   WHERE t1.tradesystemid = t2.tradesystemid 
                        AND t2.settlementgroupid = t3.settlementgroupid 
                        AND t3.brokersystemid = %s"""
        cursor.execute(sql, (broker_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        last_trading_day = str(row[1])
        logger.info("[get current trading day] current_trading_day = %s, last_trading_day = %s" % (current_trading_day, last_trading_day))

        logger.info("[get next trading day]......")

        # 判断是否跳过节假日
        holiday = conf.get("holiday")
        if holiday is True or holiday is None:
            sql = """SELECT DAY FROM siminfo.t_TradingCalendar t WHERE t.day > %s AND t.tra = '1' ORDER BY DAY LIMIT 1"""
        else:
            sql = """SELECT DAY FROM siminfo.t_TradingCalendar t WHERE t.day > %s ORDER BY DAY LIMIT 1"""
        cursor.execute(sql, (current_trading_day,))
        row = cursor.fetchone()

        next_trading_day = str(row[0])
        logger.info("[get next trading day] next_trading_day = %s" % next_trading_day)

        # 投资者资金预处理
        sql = """UPDATE siminfo.t_investorfund t1
                                     SET t1.prebalance = t1.balance, 
                                     t1.available = t1.balance, 
                                     t1.prestockvalue = t1.stockvalue, 
                                     t1.PreMargin = t1.CurrMargin,
                                     t1.stockvalue = 0,
                                     t1.premium = 0,
                                     t1.currmargin = 0, 
                                     t1.fee = 0,
                                     t1.premonthasset = IF(MONTH(%s) - MONTH(%s) = 0, t1.premonthasset, t1.currentasset),
                                     t1.preweekasset = IF(WEEK(%s, 1) - WEEK(%s, 1) = 0, t1.preweekasset, t1.currentasset),
                                     t1.preasset = t1.currentasset,
                                     t1.currentasset = t1.balance
                                   WHERE t1.brokersystemid = %s"""
        cursor.execute(sql, (current_trading_day, last_trading_day, current_trading_day, last_trading_day, broker_system_id,))

        for settlement_groups in conf.get("settlementGroups"):
            settlement_group_id = settlement_groups.get("settlementGroupId")
            settlement_id = settlement_groups.get("settlementId")

            # 检查结算状态
            logger.info("[check %s settlement status]......" % settlement_group_id)
            sql = """SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.settlementstatus
                        FROM dbclear.t_settlement t1
                        WHERE t1.tradingday = %s
                          AND t1.settlementgroupid = %s
                          AND t1.settlementid = %s for update"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            row = cursor.fetchone()
            if row is None:
                logger.error("[publish future broker] Error: There is no data for %s-%s."
                             % (settlement_group_id, settlement_id))
                result_code = -1
            elif row[3] == '0':
                logger.error("[publish future broker] Error: Settlement for %s-%s has not done."
                             % (settlement_group_id, settlement_id))
                result_code = -1
            elif row[3] == '2':
                logger.error("[publish future broker] Error: Settlement for %s-%s has been published."
                             % (settlement_group_id, settlement_id))
                result_code = -1
            else:
                # 更新客户持仓 t_clientposition
                logger.info("[update %s client position]......" % settlement_group_id)
                sql = """DELETE FROM siminfo.t_clientposition WHERE settlementgroupid = %s"""
                cursor.execute(sql, (settlement_group_id,))
                sql = """INSERT INTO siminfo.t_clientposition (TradingDay,SettlementGroupID,SettlementID,HedgeFlag,
                                      PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,
                                      YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,
                                      UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,
                                      InstrumentID,ParticipantID,ClientID 
                            )SELECT %s,
                                    SettlementGroupID,
                                    SettlementID,
                                    HedgeFlag,
                                    PosiDirection,
                                    Position,
                                    0,
                                    0,
                                    0,
                                    LongFrozen,
                                    ShortFrozen,
                                    0,
                                    0,
                                    0,
                                    (PositionCost + YdPositionCost) as PositionCost,
                                    UseMargin,
                                    0,
                                    0,
                                    0,
                                    FrozenPremium,
                                    InstrumentID,
                                    ParticipantID,
                                    ClientID 
                            FROM
                                dbclear.t_clientposition t 
                            WHERE
                                t.tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s AND t.Position != 0"""
                cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

                # 更新会员持仓 t_partposition
                logger.info("[update %s part position]......" % settlement_group_id)
                sql = """DELETE FROM siminfo.t_partposition WHERE settlementgroupid = %s"""
                cursor.execute(sql, (settlement_group_id,))
                sql = """INSERT INTO siminfo.t_partposition ( TradingDay, SettlementGroupID, SettlementID, HedgeFlag, PosiDirection, YdPosition, Position, LongFrozen, ShortFrozen, YdLongFrozen, YdShortFrozen, InstrumentID, ParticipantID, TradingRole ) SELECT
                            %s,
                            SettlementGroupID,
                            SettlementID,
                            HedgeFlag,
                            PosiDirection,
                            Position,
                            0,
                            0,
                            0,
                            LongFrozen,
                            ShortFrozen,
                            InstrumentID,
                            ParticipantID,
                            TradingRole 
                            FROM
                                dbclear.t_partposition t 
                            WHERE
                                t.tradingday = %s 
                                AND t.settlementgroupid = %s
                                AND t.settlementid = %s"""
                cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

                # 更新客户资金 t_clientfund
                logger.info("[update %s client fund]......" % settlement_group_id)
                sql = """DELETE FROM siminfo.t_clientfund WHERE settlementgroupid = %s"""
                cursor.execute(sql, (settlement_group_id,))
                sql = """INSERT INTO siminfo.t_clientfund ( TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, Available, TransFee, DelivFee, PositionMargin, Profit, StockValue )SELECT
                                %s,
                                SettlementGroupID,
                                SettlementID,
                                ParticipantID,
                                ClientID,
                                AccountID,
                                Available,
                                TransFee,
                                DelivFee,
                                PositionMargin, 
                                Profit,
                                StockValue 
                                FROM
                                    dbclear.t_clientfund t 
                                WHERE
                                    t.tradingday = %s
                                    AND t.settlementgroupid = %s
                                    AND t.settlementid = %s
                                    AND (
                                        t.available != 0 
                                        OR t.transfee != 0 
                                        OR t.delivfee != 0 
                                        OR t.positionmargin != 0 
                                        OR t.profit != 0 
                                    OR t.stockvalue != 0 )"""
                cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

                # 更新投资者资金 t_investorfund
                logger.info("[update %s investor fund]......" % settlement_group_id)
                sql = """UPDATE siminfo.t_investorfund t1,
                                (SELECT
                                        t3.brokersystemid,
                                        t1.investorid,
                                        t2.stockvalue,
                                        t2.available,
                                        t2.transfee,
                                        t2.DelivFee,
                                        t2.positionmargin,
                                        t2.profit,
                                        t2.stockvalue
                                    FROM
                                        siminfo.t_investorclient t1,
                                        siminfo.t_clientfund t2,
                                        siminfo.t_brokersystemsettlementgroup t3 
                                    WHERE
                                        t1.settlementgroupid = t2.settlementgroupid 
                                        AND t1.settlementgroupid = t3.settlementgroupid 
                                        AND t1.clientid = t2.clientid 
                                        AND t2.tradingday = %s 
                                        AND t1.settlementgroupid = %s 
                                        AND t2.settlementid = %s
                                    ) t2 
                                    SET t1.balance = t1.balance + t2.available - t2.transfee - t2.DelivFee + t2.profit,
                                    t1.available = t1.available + t2.available - t2.transfee - t2.DelivFee + t2.profit - t2.positionmargin,
                                    t1.fee = t1.fee + t2.transfee,
                                    t1.currmargin = t1.currmargin + t2.positionmargin,
                                    t1.premium = t1.premium + t2.available,
                                    t1.currentasset = t1.currentasset + t2.available - t2.transfee - t2.DelivFee + t2.stockvalue + t2.profit
                                WHERE
                                    t1.brokersystemid = t2.brokersystemid 
                                    AND t1.investorid = t2.investorid"""
                cursor.execute(sql, (next_trading_day, settlement_group_id, settlement_id))

                # 更新行情 t_marketdata
                logger.info("[update %s marketdata]......" % settlement_group_id)
                sql = """DELETE FROM siminfo.t_marketdata WHERE settlementgroupid = %s"""
                cursor.execute(sql, (settlement_group_id,))
                sql = """INSERT INTO siminfo.t_marketdata (TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                PreClosePrice,UnderlyingClosePx,PreOpenInterest,OpenPrice,HighestPrice,LowestPrice,Volume,Turnover,
                                OpenInterest,ClosePrice,SettlementPrice,UpperLimitPrice,LowerLimitPrice,PreDelta,
                                CurrDelta,UpdateTime,UpdateMillisec,InstrumentID) SELECT
                                %s,
                                SettlementGroupID,
                                NULL,
                                SettlementPrice,
                                ClosePrice,
                                UnderlyingClosePx,
                                OpenInterest,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                NULL,
                                UpdateTime,
                                UpdateMillisec,
                                InstrumentID 
                                FROM dbclear.t_marketdata t 
                                WHERE t.tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
                cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

                # 更新行情 t_FuturePositionDtl
                logger.info("[update %s t_FuturePositionDtl]......" % settlement_group_id)
                sql = """DELETE FROM siminfo.t_FuturePositionDtl WHERE settlementgroupid = %s"""
                cursor.execute(sql, (settlement_group_id,))
                sql = """INSERT into siminfo.t_FuturePositionDtl (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,Volume,OpenPrice,TradeType,CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,SettlementPrice,CloseVolume,CloseAmount)
                        select %s,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,Volume,OpenPrice,TradeType,CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,SettlementPrice,CloseVolume,CloseAmount
                        from dbclear.t_FuturePositionDtl t 
                        WHERE t.volume !=0 and t.tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
                cursor.execute(sql, (next_trading_day, current_trading_day, settlement_group_id, settlement_id))

                # 更新结算状态
                logger.info("[update %s settlement status]......" % settlement_group_id)
                sql = """UPDATE dbclear.t_settlement SET settlementstatus = '2' 
                          WHERE tradingday = %s AND settlementgroupid = %s 
                          AND settlementid = %s AND settlementstatus = '1'"""
                cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        mysql_conn.commit()
    except Exception as e:
        logger.error("[publish future broker] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[publish future broker] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(publish_future(context, conf))


if __name__ == "__main__":
    main()
