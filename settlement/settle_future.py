# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="Settlefuture")

    settlement_group_id = conf.get("settlementGroupId")
    settlement_id = conf.get("settlementId")

    logger.info("[settle future %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT t1.tradingday 
                  FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2 
                  WHERE t1.tradesystemid = t2.tradesystemid AND t2.settlementgroupid = %s"""
        cursor.execute(sql, (settlement_group_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % current_trading_day)

        logger.info("[get next trading day]......")
        sql = """SELECT DAY FROM siminfo.t_TradingCalendar t WHERE t.day > %s AND t.tra = '1' ORDER BY DAY LIMIT 1"""
        cursor.execute(sql, (current_trading_day,))
        row = cursor.fetchone()

        next_trading_day = str(row[0])
        logger.info("[get next trading day] next_trading_day = %s" % (next_trading_day))

        # 检查结算状态
        logger.info("[check settlement status]......")
        sql = """SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.settlementstatus
                    FROM dbclear.t_settlement t1
                    WHERE t1.tradingday = %s
                      AND t1.settlementgroupid = %s
                      AND t1.settlementid = %s for update"""
        cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        row = cursor.fetchone()

        if row is None:
            logger.error("[settle future] Error: There is no data for %s-%s." % (settlement_group_id, settlement_id))
            result_code = -1
        elif row[3] != '0':
            logger.error("[settle future] Error: Settlement for %s-%s has done." % (settlement_group_id, settlement_id))
            result_code = -1
        else:
            # 计算结算价
            logger.info("[calculate settlement price] is processing......")
            sql = """UPDATE dbclear.t_marketdata tm,
                        (
                            SELECT
                                t.tradingday,
                                t.settlementgroupid,
                                t.settlementid,
                                t.instrumentid,
                            CASE
                                WHEN t.Volume = 0 THEN
                                    t.ClosePrice ELSE round( t.Turnover / t.Volume, 2 ) 
                                END AS settlementprice 
                            FROM
                                dbclear.t_marketdata t 
                            WHERE
                                t.tradingday = %s 
                                AND t.settlementgroupid = %s 
                                AND t.settlementid = %s
                            ) tt 
                            SET tm.settlementprice = tt.settlementprice 
                        WHERE
                            tm.settlementgroupid = tt.settlementgroupid 
                            AND tm.settlementid = tt.settlementid 
                            AND tm.instrumentid = tt.instrumentid 
                            AND tm.tradingday = tt.tradingday"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 结算价为零赋值为昨结算
            sql = """UPDATE dbclear.t_marketdata t 
                        SET t.SettlementPrice = t.PreSettlementPrice 
                        WHERE
                            t.TradingDay = %s
                            AND t.SettlementID = %s
                            AND t.SettlementGroupID = %s 
                            AND t.SettlementPrice = %s"""
            cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, 0))

            # 计算盈亏
            logger.info("[Calculate ClientProfit] is processing......")
            sql = """insert into dbclear.t_ClientProfit(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, InstrumentID, TradeID, Direction, OffsetFlag, TradePrice, Volume, Profit)
                       select t1.tradingday,
                       t1.settlementgroupid,
                       t1.settlementid,
                       t1.participantid,
                       t1.clientid,
                       t3.accountid,
                       t1.instrumentid,
                       t1.tradeid,
                       t1.direction,
                       t1.offsetflag,
                       t1.price as tradeprice,
                       t1.volume,
                       case
                         when t1.offsetflag = '0' or t1.offsetflag = '1' or
                              t1.offsetflag = '2' or t1.offsetflag = '3' then
                          round(t4.volumemultiple * if(t1.direction='0',
                                       (t2.settlementprice - t1.price) * t1.volume,
                                       (t1.price - t2.settlementprice) * t1.volume),
                                2)
                         when t1.offsetflag = '4' then
                          round(t4.volumemultiple * if(t1.direction='0',
                                       (t2.presettlementprice - t1.price) *
                                       t1.volume,
                                       (t1.price - t2.presettlementprice) *
                                       t1.volume),
                                2)
                       end as profit
                  from dbclear.t_trade t1, dbclear.t_marketdata t2, (select t3.settlementgroupid,
                              t2.participantid,
                              t1.clientid,
                              t1.tradingrole,
                              t3.accountid
                            from siminfo.t_client t1, siminfo.t_partclient t2, siminfo.t_partroleaccount t3
                            where t1.clientid = t2.clientid
                            and t2.participantid = t3.participantid
                            and t1.tradingrole = t3.tradingrole
                            and t3.settlementgroupid = %s) t3, siminfo.t_instrument t4
                  where t1.tradingday = t2.tradingday
                    and t1.settlementgroupid = t2.settlementgroupid
                    and t1.settlementid = t2.settlementid
                    and t1.instrumentid = t2.instrumentid
                    and t1.settlementgroupid = t3.settlementgroupid
                    and t1.clientid = t3.clientid
                    and t1.settlementgroupid = t4.settlementgroupid
                    and t1.instrumentid = t4.instrumentid
                    and t1.tradingday = %s
                    and t1.settlementgroupid = %s
                    and t1.settlementid = %s
                  union all
                  select t1.tradingday,
                    t1.settlementgroupid,
                    t1.settlementid,
                    t1.participantid,
                    t1.clientid,
                    t3.accountid,
                    t1.instrumentid,
                    '--' as tradeid,
                    if(t1.posidirection='2', '0', '1') as direction,
                    '5'as offsetflag,
                    t2.settlementprice as tradeprice,
                    t1.ydposition as volume,
                    round(t4.volumemultiple * if(t1.posidirection='2',
                        (t2.settlementprice - t2.presettlementprice) * t1.ydposition,
                        (t2.presettlementprice - t2.settlementprice) * t1.ydposition), 2) as profit
                  from dbclear.t_clientposition t1, dbclear.t_marketdata t2, (select t3.settlementgroupid,
                              t2.participantid,
                              t1.clientid,
                              t1.tradingrole,
                              t3.accountid
                            from siminfo.t_client t1, siminfo.t_partclient t2, siminfo.t_partroleaccount t3
                            where t1.clientid = t2.clientid
                            and t2.participantid = t3.participantid
                            and t1.tradingrole = t3.tradingrole
                            and t3.settlementgroupid = %s) t3, siminfo.t_instrument t4
                  where t1.tradingday = t2.tradingday
                    and t1.settlementgroupid = t2.settlementgroupid
                    and t1.settlementid = t2.settlementid
                    and t1.instrumentid = t2.instrumentid
                    and t1.settlementgroupid = t3.settlementgroupid
                    and t1.clientid = t3.clientid
                    and t1.settlementgroupid = t4.settlementgroupid
                    and t1.instrumentid = t4.instrumentid
                    and t1.tradingday = %s
                    and t1.settlementgroupid = %s
                    and t1.settlementid = %s"""
            cursor.execute(sql, (settlement_group_id, current_trading_day, settlement_group_id, settlement_id,
                                 settlement_group_id, current_trading_day, settlement_group_id, settlement_id))
            # 交收持仓处理
            # 交割手续费
            # 交易手续费
            # 持仓保证金
            # 持仓盈亏
            # 客户资金
            # 会员资金
            # 更新sim表

            # 计算交易手续费
            logger.info("[calculate trade trans fee]......")
            sql = """DELETE FROM dbclear.t_clienttransfee WHERE settlementgroupid = %s AND settlementid = %s"""
            cursor.execute(sql, (settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee (TradingDay,SettlementGroupID,SettlementID,ParticipantID,
                                                          ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,
                                                          InstrumentID,TradeID,OrderSysID,Direction,TradingRole,
                                                          HedgeFlag,OffsetFlag,Volume,Price,TransFeeRatio,ValueMode,
                                                          MinFee,MaxFee,TransFee) 
                    SELECT t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,t1.accountid,
                            t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,t1.tradeid,t1.ordersysid,
                            t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THENt2.closetodayfeeratio 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS transfeeratio,
                            t2.valuemode,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.minopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.minclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS minfee,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.maxopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.maxclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS maxfee,
                        IF(t2.valuemode = '2',
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.volume * t3.volumemultiple,2),
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.price * t1.volume * t3.volumemultiple,2)) AS transfee 
                  FROM dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                  WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                          AND t2.participantid = '00000000' AND t2.clientid = '00000000' AND t1.instrumentid = t2.instrumentid
                          AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                          AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                          AND t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee (TradingDay,SettlementGroupID,SettlementID,ParticipantID,
                                                          ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,
                                                          InstrumentID,TradeID,OrderSysID,Direction,TradingRole,
                                                          HedgeFlag,OffsetFlag,Volume,Price,TransFeeRatio,ValueMode,
                                                          MinFee,MaxFee,TransFee) 
                    SELECT t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,t1.accountid,
                            t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,t1.tradeid,t1.ordersysid,
                            t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THENt2.closetodayfeeratio 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS transfeeratio,
                            t2.valuemode,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.minopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.minclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS minfee,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.maxopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.maxclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS maxfee,
                        IF(t2.valuemode = '2',
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.volume * t3.volumemultiple,2),
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.price * t1.volume * t3.volumemultiple,2)) AS transfee 
                  FROM dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                  WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                          AND t2.participantid = t1.participantid AND t2.clientid = '00000000' AND t1.instrumentid = t2.instrumentid
                          AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                          AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                          AND t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee (TradingDay,SettlementGroupID,SettlementID,ParticipantID,
                                                          ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,
                                                          InstrumentID,TradeID,OrderSysID,Direction,TradingRole,
                                                          HedgeFlag,OffsetFlag,Volume,Price,TransFeeRatio,ValueMode,
                                                          MinFee,MaxFee,TransFee) 
                    SELECT t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,t1.accountid,
                            t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,t1.tradeid,t1.ordersysid,
                            t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THENt2.closetodayfeeratio 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS transfeeratio,
                            t2.valuemode,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.minopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.minclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS minfee,
                        CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.maxopenfee 
                            WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.maxclosefee 
                            WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio END AS maxfee,
                        IF(t2.valuemode = '2',
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.volume * t3.volumemultiple,2),
                            round((CASE WHEN t1.offsetflag = '0' OR t1.offsetflag = '2' THEN t2.openfeeratio 
                                        WHEN t1.offsetflag = '3' OR t1.offsetflag = '1' THEN t2.closetodayfeeratio 
                                        WHEN t1.offsetflag = '4' THEN t2.closeyesterdayfeeratio 
                                        END ) * t1.price * t1.volume * t3.volumemultiple,2)) AS transfee 
                  FROM dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                  WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                          AND t2.participantid = t1.participantid AND t2.clientid = t1.clientid AND t1.instrumentid = t2.instrumentid
                          AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                          AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                          AND t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))



        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle future] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle future] end")
    return result_code


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_future(context, conf))


if __name__ == "__main__":
    main()