# -*- coding: UTF-8 -*-

import json
from bs_module import *

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="Settlefuture")

    settlement_group_id = conf.get("settlementGroupId")
    settlement_id = conf.get("settlementId")
    exchange_id = conf.get("exchangeId")
    marginSingleBigSide = conf.get("marginSingleBigSide")

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
            # 收盘价为零赋值为最新价
            sql = """UPDATE dbclear.t_marketdata t 
                                               SET t.ClosePrice = t.LastPrice 
                                               WHERE
                                                   t.TradingDay = %s
                                                   AND t.SettlementID = %s
                                                   AND t.SettlementGroupID = %s 
                                                   AND t.ClosePrice = %s"""
            cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, 0))
            # 清除数据
            logger.info("[delete t_delivinstrument ... ]")
            sql = "delete from dbclear.t_delivinstrument where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clientdelivfee ... ]")
            sql = "delete from dbclear.t_clientdelivfee where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clienttransfee ... ]")
            sql = "delete from dbclear.t_clienttransfee where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clientpositionmargin ... ]")
            sql = "delete from dbclear.t_clientpositionmargin where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clienttradeprofit ... ]")
            sql = "delete from dbclear.t_clienttradeprofit where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clientPositionProfit ... ]")
            sql = "delete from dbclear.t_clientPositionProfit where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            logger.info("[delete t_clientpositionpremium ... ]")
            sql = "delete from dbclear.t_clientpositionpremium where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))

            # 计算持仓明细
            calc_future_posdtl(logger, cursor, current_trading_day, settlement_group_id, settlement_id, exchange_id)
            # 期货结算
            sett_future(logger, cursor, current_trading_day, next_trading_day, settlement_group_id, settlement_id)
            # 期货期权计算
            sett_future_option(logger, cursor, current_trading_day, next_trading_day, settlement_group_id,
                               settlement_id)
            # 计算客户资金
            logger.info("[Calculate ClientFund] is processing......")
            # 1）更新positionmargin
            if marginSingleBigSide:
                sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                              (select t.tradingday,
                                           t.settlementgroupid,
                                           t.settlementid,
                                           t.participantid,
                                           t.clientid,
                                           t.accountid,
                                           0,
                                           0,
                                           sum(t.positionmargin) as positionmargin,
                                           0,
                                           0,
                                           0
                                    from (select t.tradingday,
                                                   t.settlementgroupid,
                                                   t.settlementid,
                                                   t.participantid,
                                                   t.clientid,
                                                   t.accountid,
                                                   t.productid,
                                                   max(t.positionmargin) as positionmargin
                                            from (select t.tradingday,
                                                           t.settlementgroupid,
                                                           t.settlementid,
                                                           t.participantid,
                                                           t.clientid,
                                                           t.accountid,
                                                           t.productid,
                                                           t.posidirection,
                                                           sum(t.positionmargin) as positionmargin
                                                    from dbclear.t_clientpositionmargin t
                                                   where t.tradingday = %s
                                                       and t.settlementgroupid = %s
                                                       and t.settlementid = %s
                                                   group by t.tradingday,
                                                            t.settlementgroupid,
                                                            t.settlementid,
                                                            t.participantid,
                                                            t.clientid,
                                                            t.accountid,
                                                            t.productid,
                                                            t.posidirection) t
                                           group by t.tradingday,
                                                    t.settlementgroupid,
                                                    t.settlementid,
                                                    t.participantid,
                                                    t.clientid,
                                                    t.accountid,
                                                    t.productid) t
                                   group by t.tradingday,
                                            t.settlementgroupid,
                                            t.settlementid,
                                            t.participantid,
                                            t.clientid,
                                            t.accountid) 
                              ON DUPLICATE KEY UPDATE dbclear.t_clientfund.positionmargin = values(positionmargin)"""
                cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            else:
                sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,sum(t.positionmargin) as positionmargin,0,0,0
                                           from dbclear.t_clientpositionmargin t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                           group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid) 
                                           ON DUPLICATE KEY UPDATE dbclear.t_clientfund.positionmargin = values(positionmargin)"""
                cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 2）更新transfee
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,sum(t.transfee) as transfee,0,0,0,0,0
                                            from dbclear.t_clienttransfee t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                            group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                            ON DUPLICATE KEY UPDATE dbclear.t_clientfund.transfee = values(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 3）更新delivfee
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,sum(t.delivfee) as delivfee,0,0,0,0
                                             from dbclear.t_clientdelivfee t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                                 group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                             ON DUPLICATE KEY UPDATE t_clientfund.delivfee = values(delivfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 4）更新profit
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,0,sum(t.profit) as profit,0,0
                                           from dbclear.t_clienttradeprofit t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                           group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                           ON DUPLICATE KEY UPDATE dbclear.t_clientfund.profit = values(profit)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 5）更新premium
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                                  (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,0,0,sum( t.Premium ) AS available,0
                                                from dbclear.t_clientpositionpremium t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                                group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                                ON DUPLICATE KEY UPDATE dbclear.t_clientfund.available = values(available)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 更新结算状态
            logger.info("[update settlement status] is processing......")
            sql = """UPDATE dbclear.t_settlement SET settlementstatus = '1' 
                              WHERE tradingday = %s AND settlementgroupid = %s AND settlementid = %s AND settlementstatus = '0'"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle future] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle future] end")
    return result_code


def sett_future(logger, cursor, current_trading_day, next_trading_day, settlement_group_id, settlement_id):
    # 计算结算价
    logger.info("[calculate settlement price] is processing......")
    sql = """UPDATE dbclear.t_marketdata tm,
                                                   (
                                                       select t1.tradingday,
                                                              t1.settlementgroupid,
                                                              t1.settlementid,
                                                              t1.instrumentid,
                                                              case
                                                                when abs(mod((t1.settlementprice - t3.presettlementprice), t2.pricetick)) <
                                                                     (t2.pricetick / 2) then
                                                                 t3.presettlementprice +
                                                                 if(sign(t1.settlementprice - t3.presettlementprice)=1,
                                                                        floor((t1.settlementprice - t3.presettlementprice) /
                                                                              t2.pricetick),
                                                                        ceil((t1.settlementprice - t3.presettlementprice) /
                                                                             t2.pricetick)) * t2.pricetick
                                                                else
                                                                 t3.presettlementprice +
                                                                 if(sign(t1.settlementprice - t3.presettlementprice)=1,
                                                                        ceil((t1.settlementprice - t3.presettlementprice) /
                                                                             t2.pricetick),
                                                                        floor((t1.settlementprice - t3.presettlementprice) /
                                                                              t2.pricetick)) * t2.pricetick
                                                              end as settlementprice
                                                         from (SELECT
                                                                       t.tradingday,
                                                                       t.settlementgroupid,
                                                                       t.settlementid,
                                                                       t.instrumentid,
                                                               CASE
                                                                       WHEN t.Volume = 0 THEN
                                                                               0 ELSE round( t.Turnover / t.Volume / t1.VolumeMultiple, 2 ) 
                                                                       END AS settlementprice 
                                                               FROM
                                                                       dbclear.t_marketdata t, siminfo.t_instrument t1
                                                               WHERE
                                                                       t.tradingday = %s
                                                                       AND t.settlementgroupid = %s
                                                                       AND t.settlementid = %s
                                                                       AND t.instrumentid = t1.instrumentid
                                                                       AND t.settlementgroupid = t1.settlementgroupid) t1,
                                                              siminfo.t_instrumentproperty t2, dbclear.t_marketdata t3
                                                        where t1.settlementgroupid = t2.settlementgroupid
                                                          and t1.instrumentid = t2.instrumentid
                                                          and t1.tradingday = t3.tradingday
                                                          and t1.settlementgroupid = t3.settlementgroupid
                                                          and t1.settlementid = t3.settlementid
                                                          and t1.instrumentid = t3.instrumentid) tt 
                                                       SET tm.settlementprice = tt.settlementprice 
                                                   WHERE
                                                       tm.settlementgroupid = tt.settlementgroupid 
                                                       AND tm.settlementid = tt.settlementid 
                                                       AND tm.instrumentid = tt.instrumentid 
                                                       AND tm.tradingday = tt.tradingday
                                                       AND tm.settlementprice = 0"""
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
    sql = """insert into dbclear.t_clienttradeprofit(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, InstrumentID, TradeID, Direction, OffsetFlag, Price, Volume, Profit)
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
                                  t1.price,
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
                                       where t1.SettlementGroupID = t2.SettlementGroupID
                                           and t1.SettlementGroupID = t3.SettlementGroupID
                                           and t1.clientid = t2.clientid
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
                               and t4.ProductClass != '2'
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
                               t2.settlementprice as price,
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
                                       where t1.SettlementGroupID = t2.SettlementGroupID
                                       and t1.SettlementGroupID = t3.SettlementGroupID 
                                       and t1.clientid = t2.clientid
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
                               and t4.ProductClass != '2'
                               and t1.tradingday = %s
                               and t1.settlementgroupid = %s
                               and t1.settlementid = %s"""
    cursor.execute(sql, (settlement_group_id, current_trading_day, settlement_group_id, settlement_id,
                         settlement_group_id, current_trading_day, settlement_group_id, settlement_id))
    # 交收持仓处理
    logger.info("[Move DelivPosition] is processing......")
    # 1）插入到t_delivinstrument表
    sql = """insert into dbclear.t_delivinstrument(TradingDay, SettlementGroupID, SettlementID, InstrumentID
                                       )select %s, t.SettlementGroupID, %s, t.instrumentid
                                   from siminfo.t_instrumentproperty t, siminfo.t_instrument t1
                               where t.SettlementGroupID = t1.SettlementGroupID and t.InstrumentID = t1.InstrumentID 
                                 and t1.ProductClass != '2' and  t.settlementgroupid = %s and t.startdelivdate <= %s"""
    cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, next_trading_day))
    # 2）插入到t_clientdelivposition
    sql = """insert into dbclear.t_clientdelivposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,
                                     PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,
                                     BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,
                                     LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID
                                   )select TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,
                                   LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,
                                   YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,
                                   InstrumentID,ParticipantID,ClientID from dbclear.t_clientposition
                                    where tradingday = %s
                                      and settlementgroupid = %s
                                      and settlementid = %s
                                      and Position != '0'
                                      and instrumentid in       
                                          (select t.instrumentid
                                             from dbclear.t_delivinstrument t
                                            where t.tradingday = %s
                                               and t.settlementgroupid = %s
                                               and t.settlementid = %s)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    # 3) 删除t_clientposition
    sql = """delete from dbclear.t_clientposition
                                        where (tradingday = %s
                                          and settlementgroupid = %s
                                          and settlementid = %s
                                          and instrumentid in
                                              (select t.instrumentid
                                                 from dbclear.t_delivinstrument t
                                                where t.tradingday = %s
                                                   and t.settlementgroupid = %s
                                                   and t.settlementid = %s))
                                          or Position = '0'"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    # 删除 t_FuturePositionDtl
    sql = """delete from dbclear.t_FuturePositionDtl
                where (tradingday = %s
                    and settlementgroupid = %s
                    and settlementid = %s
                    and instrumentid in
                            (select t.instrumentid
                                 from dbclear.t_delivinstrument t
                                where t.tradingday = %s
                                     and t.settlementgroupid = %s
                                     and t.settlementid = %s))"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))

    # 交割手续费
    logger.info("[Calculate DelivFee] is processing......")
    # 插入t_clientdelivfee表中
    sql = """insert into dbclear.t_clientdelivfee(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,Position,Price,DelivFeeRatio,ValueMode,DelivFee
                                       )select t1.tradingday,
                                              t1.settlementgroupid,
                                              t1.settlementid,
                                              t1.participantid,
                                              t1.clientid,
                                              t2.accountid,
                                              t3.productgroupid,
                                              t3.productid,
                                              t3.underlyinginstrid,
                                              t1.instrumentid,
                                              t1.position,
                                              t4.settlementprice as Price,
                                              t2.delivfeeratio,
                                              t2.valuemode,
                                              round(if(t2.valuemode='2',
                                                     round(t2.delivfeeratio * t1.position * t3.volumemultiple, 2),
                                                     round(t2.delivfeeratio * t4.settlementprice * t1.position *
                                                           t3.volumemultiple,
                                                           2)), 2) as delivfee
                                       from (select t.tradingday,
                                                  t.settlementgroupid,
                                                  t.settlementid,
                                                  t.participantid,
                                                  t.clientid,
                                                  t.instrumentid,
                                                  abs(sum(if(t.posidirection='2',
                                                                 (t.position + t.ydposition),
                                                                 -1 * (t.position + t.ydposition)))) as position
                                           from dbclear.t_clientdelivposition t
                                            where t.tradingday = %s
                                              and t.settlementgroupid = %s
                                              and t.settlementid = %s
                                            group by t.tradingday,
                                                     t.settlementgroupid,
                                                     t.settlementid,
                                                     t.participantid,
                                                     t.clientid,
                                                     t.instrumentid) t1,
                                          (select t1.SettlementGroupID,
                                                  t1.ParticipantID,
                                                  t1.ClientID,
                                                  t2.AccountID,
                                                  t1.InstrumentID,
                                                  t1.DelivFeeRatio,
                                                  t1.ValueMode
                                             from siminfo.t_delivfeeratedetail t1, siminfo.t_partroleaccount t2
                                             where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                          siminfo.t_instrument t3,
                                          dbclear.t_marketdata t4
                                       where t1.settlementgroupid = t2.settlementgroupid
                                       and t2.participantid = '00000000'
                                       and t2.clientid = '00000000'
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.instrumentid = t3.instrumentid
                                       and t1.tradingday = t4.tradingday
                                       and t1.settlementgroupid = t4.settlementgroupid
                                       and t1.settlementid = t4.settlementid
                                       and t1.instrumentid = t4.instrumentid
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clientdelivfee(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,Position,Price,DelivFeeRatio,ValueMode,DelivFee
                                                 )select t1.tradingday,
                                                          t1.settlementgroupid,
                                                          t1.settlementid,
                                                          t1.participantid,
                                                          t1.clientid,
                                                          t2.accountid,
                                                          t3.productgroupid,
                                                          t3.productid,
                                                          t3.underlyinginstrid,
                                                          t1.instrumentid,
                                                          t1.position,
                                                          t4.settlementprice as Price,
                                                          t2.delivfeeratio,
                                                          t2.valuemode,
                                                          round(if(t2.valuemode='2',
                                                                 round(t2.delivfeeratio * t1.position * t3.volumemultiple, 2),
                                                                 round(t2.delivfeeratio * t4.settlementprice * t1.position *
                                                                       t3.volumemultiple,
                                                                       2)), 2) as delivfee
                                                   from (select t.tradingday,
                                                              t.settlementgroupid,
                                                              t.settlementid,
                                                              t.participantid,
                                                              t.clientid,
                                                              t.instrumentid,
                                                              abs(sum(if(t.posidirection='2',
                                                                             (t.position + t.ydposition),
                                                                             -1 * (t.position + t.ydposition)))) as position
                                                       from dbclear.t_clientdelivposition t
                                                        where t.tradingday = %s
                                                          and t.settlementgroupid = %s
                                                          and t.settlementid = %s
                                                        group by t.tradingday,
                                                                 t.settlementgroupid,
                                                                 t.settlementid,
                                                                 t.participantid,
                                                                 t.clientid,
                                                                 t.instrumentid) t1,
                                                      (select t1.SettlementGroupID,
                                                              t1.ParticipantID,
                                                              t1.ClientID,
                                                              t2.AccountID,
                                                              t1.InstrumentID,
                                                              t1.DelivFeeRatio,
                                                              t1.ValueMode
                                                         from siminfo.t_delivfeeratedetail t1, siminfo.t_partroleaccount t2
                                                         where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                                      siminfo.t_instrument t3,
                                                      dbclear.t_marketdata t4
                                                   where t1.settlementgroupid = t2.settlementgroupid
                                                   and t2.participantid = t1.participantid
                                                   and t2.clientid = '00000000'
                                                   and t1.instrumentid = t2.instrumentid
                                                   and t1.settlementgroupid = t3.settlementgroupid
                                                   and t1.instrumentid = t3.instrumentid
                                                   and t1.tradingday = t4.tradingday
                                                   and t1.settlementgroupid = t4.settlementgroupid
                                                   and t1.settlementid = t4.settlementid
                                                   and t1.instrumentid = t4.instrumentid
                                                   and t1.tradingday = %s
                                                   and t1.settlementgroupid = %s
                                                   and t1.settlementid = %s
                                         ON DUPLICATE KEY UPDATE delivfeeratio = VALUES(delivfeeratio), valuemode = VALUES(valuemode),
                                               delivfee = VALUES(delivfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clientdelivfee(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,Position,Price,DelivFeeRatio,ValueMode,DelivFee
                                                 )select t1.tradingday,
                                                          t1.settlementgroupid,
                                                          t1.settlementid,
                                                          t1.participantid,
                                                          t1.clientid,
                                                          t2.accountid,
                                                          t3.productgroupid,
                                                          t3.productid,
                                                          t3.underlyinginstrid,
                                                          t1.instrumentid,
                                                          t1.position,
                                                          t4.settlementprice as prcie,
                                                          t2.delivfeeratio,
                                                          t2.valuemode,
                                                          round(if(t2.valuemode='2',
                                                                 round(t2.delivfeeratio * t1.position * t3.volumemultiple, 2),
                                                                 round(t2.delivfeeratio * t4.settlementprice * t1.position *
                                                                       t3.volumemultiple,
                                                                       2)), 2) as delivfee
                                                   from (select t.tradingday,
                                                              t.settlementgroupid,
                                                              t.settlementid,
                                                              t.participantid,
                                                              t.clientid,
                                                              t.instrumentid,
                                                              abs(sum(if(t.posidirection='2',
                                                                             (t.position + t.ydposition),
                                                                             -1 * (t.position + t.ydposition)))) as position
                                                       from dbclear.t_clientdelivposition t
                                                        where t.tradingday = %s
                                                          and t.settlementgroupid = %s
                                                          and t.settlementid = %s
                                                        group by t.tradingday,
                                                                 t.settlementgroupid,
                                                                 t.settlementid,
                                                                 t.participantid,
                                                                 t.clientid,
                                                                 t.instrumentid) t1,
                                                      (select t1.SettlementGroupID,
                                                              t1.ParticipantID,
                                                              t1.ClientID,
                                                              t2.AccountID,
                                                              t1.InstrumentID,
                                                              t1.DelivFeeRatio,
                                                              t1.ValueMode
                                                         from siminfo.t_delivfeeratedetail t1, siminfo.t_partroleaccount t2
                                                         where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                                      siminfo.t_instrument t3,
                                                      dbclear.t_marketdata t4
                                                   where t1.settlementgroupid = t2.settlementgroupid
                                                   and t2.participantid = t1.participantid
                                                   and t2.clientid = t1.clientid
                                                   and t1.instrumentid = t2.instrumentid
                                                   and t1.settlementgroupid = t3.settlementgroupid
                                                   and t1.instrumentid = t3.instrumentid
                                                   and t1.tradingday = t4.tradingday
                                                   and t1.settlementgroupid = t4.settlementgroupid
                                                   and t1.settlementid = t4.settlementid
                                                   and t1.instrumentid = t4.instrumentid
                                                   and t1.tradingday = %s
                                                   and t1.settlementgroupid = %s
                                                   and t1.settlementid = %s
                                         ON DUPLICATE KEY UPDATE delivfeeratio = VALUES(delivfeeratio), valuemode = VALUES(valuemode),
                                               delivfee = VALUES(delivfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))

    # 交易手续费
    logger.info("[Calculate TransFee] is processing......")
    # 插入t_clienttransfee表中
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
                                   )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                      t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                                      t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                                      case
                                        when t1.offsetflag = '0' or
                                             t1.offsetflag = '2' then
                                         t2.openfeeratio
                                        when t1.offsetflag = '3' or t1.offsetflag = '1'  then
                                         t2.closetodayfeeratio
                                        when t1.offsetflag = '4' then
                                         t2.closeyesterdayfeeratio
                                      end as transfeeratio,
                                      t2.valuemode,
                                      if(t2.valuemode='2',
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.volume,
                                                   2),
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.price * t1.volume * t3.volumemultiple,
                                                   2)) as transfee,
                                                       t1.OrderSysID,
                                                       '0' as Minfee,
                                                       '0' as MaxFee
                                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                       where t1.TradingDay = t2.TradingDay
                                       and t1.SettlementID = t2.SettlementID
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t2.participantid = '00000000'
                                       and t2.clientid = '00000000'
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.instrumentid = t3.instrumentid
                                       and t3.ProductClass != '2'
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
                                     )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                      t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                                      t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                                      case
                                        when t1.offsetflag = '0' or
                                             t1.offsetflag = '2' then
                                         t2.openfeeratio
                                        when t1.offsetflag = '3' or t1.offsetflag = '1'  then
                                         t2.closetodayfeeratio
                                        when t1.offsetflag = '4' then
                                         t2.closeyesterdayfeeratio
                                      end as transfeeratio,
                                      t2.valuemode,
                                      if(t2.valuemode='2',
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.volume,
                                                   2),
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.price * t1.volume * t3.volumemultiple,
                                                   2)) as transfee,
                                                       t1.OrderSysID,
                                                       '0' as Minfee,
                                                       '0' as MaxFee
                                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                       where t1.TradingDay = t2.TradingDay
                                       and t1.SettlementID = t2.SettlementID
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t2.participantid = t1.participantid 
                                       and t2.clientid = '00000000'
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.instrumentid = t3.instrumentid
                                       and t3.ProductClass != '2'
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s
                                       ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                               transfee = VALUES(transfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
                                   )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                      t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                                      t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                                      case
                                        when t1.offsetflag = '0' or
                                             t1.offsetflag = '2' then
                                         t2.openfeeratio
                                        when t1.offsetflag = '3' or t1.offsetflag = '1'  then
                                         t2.closetodayfeeratio
                                        when t1.offsetflag = '4' then
                                         t2.closeyesterdayfeeratio
                                      end as transfeeratio,
                                      t2.valuemode,
                                      if(t2.valuemode='2',
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.volume,
                                                   2),
                                             round((case
                                                     when t1.offsetflag = '0' or
                                                          t1.offsetflag = '2' then
                                                      t2.openfeeratio
                                                     when t1.offsetflag = '3' or t1.offsetflag = '1' then
                                                      t2.closetodayfeeratio
                                                     when t1.offsetflag = '4' then
                                                      t2.closeyesterdayfeeratio
                                                   end) * t1.price * t1.volume * t3.volumemultiple,
                                                   2)) as transfee,
                                                       t1.OrderSysID,
                                                       '0' as Minfee,
                                                       '0' as MaxFee
                                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                       where t1.TradingDay = t2.TradingDay
                                       and t1.SettlementID = t2.SettlementID
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t2.participantid = t1.participantid 
                                       and t2.clientid = t1.clientid
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.instrumentid = t3.instrumentid
                                       and t3.ProductClass != '2'
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s
                                       ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                               transfee = VALUES(transfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    # 持仓保证金
    logger.info("[Calculate PositionMargin] is processing......")
    # 插入t_clientpositionmargin表中
    sql = """insert into dbclear.t_clientpositionmargin(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,TradingRole,HedgeFlag,PosiDirection,Position,MarginRatio,ValueMode,SettlementPrice,PositionMargin
                                     )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                       t2.accountid,t4.productgroupid,t4.productid,t4.underlyinginstrid,t1.instrumentid,t1.tradingrole,
                                       t1.hedgeflag,t1.posidirection,t1.position + t1.ydposition,
                                       if(t1.posidirection='2',
                                         t2.longmarginratio,
                                         t2.shortmarginratio) as MarginRatio,
                                       t2.valuemode,t3.settlementprice,
                                       round(if(t2.valuemode='1',
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) *
                                               t4.volumemultiple * t3.settlementprice,
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) * t4.volumemultiple),
                                        2) as positionmargin
                                       from (select t1.*, t2.tradingrole
                                           from dbclear.t_clientposition t1, siminfo.t_client t2
                                           where t1.clientid = t2.clientid) t1,
                                       (select t1.settlementgroupid,
                                               t1.participantid,
                                               t2.accountid,
                                               t1.clientid,
                                               t1.instrumentid,
                                               t2.tradingrole,
                                               t1.hedgeflag,
                                               t1.longmarginratio,
                                               t1.shortmarginratio,
                                               t1.valuemode
                                        from siminfo.t_marginratedetail t1, siminfo.t_partroleaccount t2
                                       where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                           dbclear.t_marketdata t3,
                                           siminfo.t_instrument t4
                                       where t2.participantid = '00000000'
                                       and t2.clientid = '00000000'
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.instrumentid = t3.instrumentid
                                       and t1.tradingday = t3.tradingday
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.settlementid = t3.settlementid
                                       and t1.settlementgroupid = t4.settlementgroupid
                                       and t1.instrumentid = t4.instrumentid
                                       and t4.ProductClass != '2'
                                       and (t1.posidirection = '2' or t1.posidirection = '3')
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s
                                       """
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clientpositionmargin(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,TradingRole,HedgeFlag,PosiDirection,Position,MarginRatio,ValueMode,SettlementPrice,PositionMargin
                                     )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                       t2.accountid,t4.productgroupid,t4.productid,t4.underlyinginstrid,t1.instrumentid,t1.tradingrole,
                                       t1.hedgeflag,t1.posidirection,t1.position + t1.ydposition,
                                       if(t1.posidirection='2',
                                         t2.longmarginratio,
                                         t2.shortmarginratio) as MarginRatio,
                                       t2.valuemode,t3.settlementprice,
                                       round(if(t2.valuemode='1',
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) *
                                               t4.volumemultiple * t3.settlementprice,
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) * t4.volumemultiple),
                                        2) as positionmargin
                                       from (select t1.*, t2.tradingrole
                                           from dbclear.t_clientposition t1, siminfo.t_client t2
                                           where t1.clientid = t2.clientid) t1,
                                       (select t1.settlementgroupid,
                                               t1.participantid,
                                               t2.accountid,
                                               t1.clientid,
                                               t1.instrumentid,
                                               t2.tradingrole,
                                               t1.hedgeflag,
                                               t1.longmarginratio,
                                               t1.shortmarginratio,
                                               t1.valuemode
                                        from siminfo.t_marginratedetail t1, siminfo.t_partroleaccount t2
                                       where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                           dbclear.t_marketdata t3,
                                           siminfo.t_instrument t4
                                       where t2.participantid = t1.participantid
                                       and t2.clientid = '00000000'
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.instrumentid = t3.instrumentid
                                       and t1.tradingday = t3.tradingday
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.settlementid = t3.settlementid
                                       and t1.settlementgroupid = t4.settlementgroupid
                                       and t1.instrumentid = t4.instrumentid
                                       and t4.ProductClass != '2'
                                       and (t1.posidirection = '2' or t1.posidirection = '3')
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s
                                       ON DUPLICATE KEY UPDATE positionmargin = VALUES(positionmargin), MarginRatio = VALUES(MarginRatio),
                                               valuemode = VALUES(valuemode)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    sql = """insert into dbclear.t_clientpositionmargin(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,TradingRole,HedgeFlag,PosiDirection,Position,MarginRatio,ValueMode,SettlementPrice,PositionMargin
                                     )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                                       t2.accountid,t4.productgroupid,t4.productid,t4.underlyinginstrid,t1.instrumentid,t1.tradingrole,
                                       t1.hedgeflag,t1.posidirection,t1.position + t1.ydposition,
                                       if(t1.posidirection='2',
                                         t2.longmarginratio,
                                         t2.shortmarginratio) as MarginRatio,
                                       t2.valuemode,t3.settlementprice,
                                       round(if(t2.valuemode='1',
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) *
                                               t4.volumemultiple * t3.settlementprice,
                                               if(t1.posidirection='2',
                                                      t2.longmarginratio,
                                                      t2.shortmarginratio) * (t1.position + t1.ydposition) * t4.volumemultiple),
                                        2) as positionmargin
                                       from (select t1.*, t2.tradingrole
                                           from dbclear.t_clientposition t1, siminfo.t_client t2
                                           where t1.clientid = t2.clientid) t1,
                                       (select t1.settlementgroupid,
                                               t1.participantid,
                                               t2.accountid,
                                               t1.clientid,
                                               t1.instrumentid,
                                               t2.tradingrole,
                                               t1.hedgeflag,
                                               t1.longmarginratio,
                                               t1.shortmarginratio,
                                               t1.valuemode
                                        from siminfo.t_marginratedetail t1, siminfo.t_partroleaccount t2
                                       where t1.SettlementGroupID = t2.SettlementGroupID) t2,
                                           dbclear.t_marketdata t3,  
                                           siminfo.t_instrument t4
                                       where t1.participantid = t1.participantid
                                       and t2.clientid = t1.clientid
                                       and t1.instrumentid = t2.instrumentid
                                       and t1.tradingrole = t2.tradingrole
                                       and t1.hedgeflag = t2.hedgeflag
                                       and t1.instrumentid = t3.instrumentid
                                       and t1.tradingday = t3.tradingday
                                       and t1.settlementgroupid = t2.settlementgroupid
                                       and t1.settlementgroupid = t3.settlementgroupid
                                       and t1.settlementid = t3.settlementid
                                       and t1.settlementgroupid = t4.settlementgroupid
                                       and t1.instrumentid = t4.instrumentid
                                       and t4.ProductClass != '2'
                                       and (t1.posidirection = '2' or t1.posidirection = '3')
                                       and t1.tradingday = %s
                                       and t1.settlementgroupid = %s
                                       and t1.settlementid = %s
                                       ON DUPLICATE KEY UPDATE positionmargin = VALUES(positionmargin), MarginRatio = VALUES(MarginRatio),
                                               valuemode = VALUES(valuemode)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
    # 持仓盈亏
    logger.info("[Calculate PositionProfit] is processing......")
    # 写入t_clientPositionProfit表中
    sql = """insert into dbclear.t_ClientPositionProfit(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, InstrumentID, HedgeFlag, PosiDirection, PositionCost, SettlementPositionCost, PositionProfit
                                   )select t1.tradingday,
                                          t1.settlementgroupid,
                                          t1.settlementid,
                                          t1.participantid,
                                          t1.clientid,
                                          t1.instrumentid,
                                          t1.hedgeflag,
                                          t1.posidirection,
                                          t1.positioncost + t1.ydpositioncost,
                                          round((t1.position + t1.ydposition) * t2.volumemultiple * t3.settlementprice, 2) as settlepositioncost,
                                          if(t1.posidirection='2', 1, -1) * round((round((t1.position + t1.ydposition) * t2.volumemultiple * t3.settlementprice, 2) - (t1.positioncost + t1.ydpositioncost)), 2) as positionprofit
                                     from dbclear.t_clientposition t1, siminfo.t_instrument t2, dbclear.t_marketdata t3
                                    where t1.tradingday = t3.tradingday
                                      and t1.settlementgroupid = t2.settlementgroupid
                                      and t1.settlementgroupid = t3.settlementgroupid
                                      and t1.settlementid = t3.settlementid
                                      and t1.instrumentid = t2.instrumentid
                                      and t1.instrumentid = t3.instrumentid
                                      and t2.ProductClass != '2'
                                      and t1.tradingday = %s
                                      and t1.settlementgroupid = %s
                                      and t1.settlementid = %s"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))


def sett_future_option(logger, cursor, current_trading_day, next_trading_day, settlement_group_id, settlement_id):
    # 计算结算价
    riskfree_interest = 0.02
    sql = """SELECT t1.instrumentid, t1.underlyinginstrid, t1.optionstype, t1.strikeprice, t2.lastprice AS optionprice, t3.settlementprice AS underlyingprice, t2.volume, 
                                  DATEDIFF(t4.expiredate, %s) + 1 AS duration, t4.pricetick
                                FROM siminfo.t_instrument t1, dbclear.t_marketdata t2, dbclear.t_marketdata t3, siminfo.t_instrumentproperty t4
                                WHERE t1.settlementgroupid = %s AND t1.OptionsType != '0' 
                                AND t1.settlementgroupid = t2.settlementgroupid AND t1.instrumentid = t2.instrumentid
                                AND t1.settlementgroupid = t3.settlementgroupid AND t1.underlyinginstrid = t3.instrumentid
                                AND t1.settlementgroupid = t4.settlementgroupid AND t1.instrumentid = t4.instrumentid
                                AND t2.tradingday = %s AND t2.settlementid = %s
                                AND t3.tradingday = %s AND t3.settlementid = %s
                                ORDER BY t1.underlyinginstrid, t1.instrumentid, t1.optionstype"""
    cursor.execute(sql, (
        current_trading_day, settlement_group_id, current_trading_day, settlement_id, current_trading_day,
        settlement_id))
    rows = cursor.fetchall()

    dce_bs = DCE_BLACKSCHOLES()
    op = Option(UNDERLYING_FUTURE, OPTIONTYPE_EUROPEAN, CALLPUT_CALL, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00)

    ins_list = []
    md_dict = {}
    for row in rows:
        underlying_id = str(row[1])
        instrument_id = str(row[0])
        options_type = str(row[2])
        strike_price = float(str(row[3]))
        option_price = float(str(row[4]))
        underlying_price = float(str(row[5]))
        trade_volume = int(str(row[6]))
        duration = int(str(row[7]))
        price_tick = float(str(row[8]))

        ins = {"instrumentID": instrument_id, "underlyingInsID": underlying_id, "optionsType": options_type,
               "strikePrice": strike_price,
               "optionPrice": option_price, "underlyingPrice": underlying_price, "duration": duration,
               "priceTick": price_tick}

        ins_list.append(ins)

        op.call_put = CALLPUT_CALL if options_type == "1" else CALLPUT_PUT
        op.strike_price = strike_price
        op.underlying_price = underlying_price
        op.t = duration
        op.r = riskfree_interest
        sigma = dce_bs.calc_sigma(op, option_price)

        total_sigma = trade_volume * sigma
        sum_sigma = sigma
        total_volume = trade_volume
        sum_count = 1
        if underlying_id in md_dict.keys():
            total_sigma += md_dict[underlying_id]["totalSigma"]
            total_volume += md_dict[underlying_id]["totalVolume"]
            sum_sigma += md_dict[underlying_id]["sumSigma"]
            sum_count += md_dict[underlying_id]["sumCount"]

        md_dict.update({underlying_id: {"totalSigma": total_sigma, "totalVolume": total_volume, "sumSigma": sum_sigma,
                                        "sumCount": sum_count}})

    for underlying_id in md_dict.keys():
        total_sigma = md_dict[underlying_id]["totalSigma"]
        total_volume = md_dict[underlying_id]["totalVolume"]
        sum_sigma = md_dict[underlying_id]["sumSigma"]
        sum_count = md_dict[underlying_id]["sumCount"]

        settle_sigma = 0
        if trade_volume == 0:
            settle_sigma = round(sum_sigma / sum_count, 4)
        else:
            settle_sigma = round(total_sigma / total_volume, 4)
        md_dict[underlying_id].update({"sigma": settle_sigma})

    sql = """update dbclear.t_marketdata t 
              SET t.SettlementPrice = %s
			  WHERE t.TradingDay = %s
              AND t.SettlementID = %s
              AND t.SettlementGroupID = %s 
              AND t.InstrumentID = %s"""
    sql_params = []
    for ins in ins_list:
        instrument_id = ins["instrumentID"]
        underlying_id = ins["underlyingInsID"]
        price_tick = ins["priceTick"]
        sigma = md_dict[underlying_id]["sigma"]

        op.call_put = CALLPUT_CALL if ins["optionsType"] == "1" else CALLPUT_PUT
        op.strike_price = ins["strikePrice"]
        op.underlying_price = ins["underlyingPrice"]
        op.t = ins["duration"]
        op.r = riskfree_interest
        op.sigma = sigma
        settle_price = dce_bs.calc_price(op)
        a, b = divmod(settle_price, price_tick)
        settle_price = price_tick * a + (0 if b < price_tick / 2 else price_tick)
        sql_params.append((settle_price, current_trading_day, settlement_id, settlement_group_id, instrument_id))
    cursor.executemany(sql, sql_params)

    # 结算价为零赋值为昨结算
    sql = """UPDATE dbclear.t_marketdata t 
            SET t.SettlementPrice = t.PreSettlementPrice 
            WHERE
                t.TradingDay = %s
                AND t.SettlementID = %s
                AND t.SettlementGroupID = %s 
                AND t.SettlementPrice = %s"""
    cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, 0))

    # 交收持仓处理
    logger.info("[Move Options DelivPosition] is processing......")
    # 1）插入到t_delivinstrument表
    sql = """insert into dbclear.t_delivinstrument(TradingDay, SettlementGroupID, SettlementID, InstrumentID
                                           )select %s, t.SettlementGroupID, %s, t.instrumentid
                                       from siminfo.t_instrumentproperty t, siminfo.t_instrument t1
                                   where t.SettlementGroupID = t1.SettlementGroupID and t.InstrumentID = t1.InstrumentID 
                                     and t1.ProductClass = '2' and  t.settlementgroupid = %s and t.startdelivdate <= %s"""
    cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, next_trading_day))
    # 2）插入到t_clientdelivposition
    sql = """insert into dbclear.t_clientdelivposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,
                                         PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,
                                         BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,
                                         LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID
                                       )select TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,
                                       LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,
                                       YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,
                                       InstrumentID,ParticipantID,ClientID from dbclear.t_clientposition
                                        where tradingday = %s
                                          and settlementgroupid = %s
                                          and settlementid = %s
                                          and Position != '0'
                                          and instrumentid in       
                                              (select t.instrumentid
                                                 from dbclear.t_delivinstrument t
                                                where t.tradingday = %s
                                                   and t.settlementgroupid = %s
                                                   and t.settlementid = %s)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    # 3) 删除t_clientposition
    sql = """delete from dbclear.t_clientposition
                                            where (tradingday = %s
                                              and settlementgroupid = %s
                                              and settlementid = %s
                                              and instrumentid in
                                                  (select t.instrumentid
                                                     from dbclear.t_delivinstrument t
                                                    where t.tradingday = %s
                                                       and t.settlementgroupid = %s
                                                       and t.settlementid = %s))
                                              or Position = '0'"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    # 删除 t_FuturePositionDtl
    sql = """delete from dbclear.t_FuturePositionDtl
                where (tradingday = %s
                    and settlementgroupid = %s
                    and settlementid = %s
                    and instrumentid in
                            (select t.instrumentid
                                 from dbclear.t_delivinstrument t
                                where t.tradingday = %s
                                     and t.settlementgroupid = %s
                                     and t.settlementid = %s))"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                         current_trading_day, settlement_group_id, settlement_id))
    # 交割手续费
    sql = """"""
    # 交易手续费
    logger.info("[Calculate Options  TransFee] is processing......")
    # 插入t_clienttransfee表中
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
                 )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                case
                        when t1.offsetflag = '0' or
                              t1.offsetflag = '2' then
                               t2.openfeeratio
                        when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                               t2.closetodayfeeratio
                end as transfeeratio,
                t2.valuemode,
                if(t2.valuemode='2',
                           round((case when t1.offsetflag = '0' or
                                       t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end),
                               2) * t1.volume ,
                           round((case
                                       when t1.offsetflag = '0' or
                                        t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end) * t1.price * t3.volumemultiple,
                               2) * t1.volume ) as transfee,
                                               t1.OrderSysID,
                                               '0' as Minfee,
                                               '0' as MaxFee
                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                       where t1.TradingDay = t2.TradingDay
                       and t1.SettlementID = t2.SettlementID
                       and t1.settlementgroupid = t2.settlementgroupid
                       and t2.participantid = '00000000'
                       and t2.clientid = '00000000'
                       and t1.instrumentid = t2.instrumentid
                       and t1.tradingrole = t2.tradingrole
                       and t1.hedgeflag = t2.hedgeflag
                       and t1.settlementgroupid = t3.settlementgroupid
                       and t1.instrumentid = t3.instrumentid
                       and t3.ProductClass = '2'
                       and t1.tradingday = %s
                       and t1.settlementgroupid = %s
                       and t1.settlementid = %s"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

    # 插入t_clienttransfee表中
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
             )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                case
                        when t1.offsetflag = '0' or
                              t1.offsetflag = '2' then
                               t2.openfeeratio
                        when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                               t2.closetodayfeeratio
                end as transfeeratio,
                t2.valuemode,
                if(t2.valuemode='2',
                           round((case when t1.offsetflag = '0' or
                                       t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end),
                               2) * t1.volume ,
                           round((case
                                       when t1.offsetflag = '0' or
                                        t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end) * t1.price * t3.volumemultiple,
                               2) * t1.volume ) as transfee,
                                               t1.OrderSysID,
                                               '0' as Minfee,
                                               '0' as MaxFee
                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                       where t1.TradingDay = t2.TradingDay
                       and t1.SettlementID = t2.SettlementID
                       and t1.settlementgroupid = t2.settlementgroupid
                       and t2.participantid = t1.participantid
                       and t2.clientid = '00000000'
                       and t1.instrumentid = t2.instrumentid
                       and t1.tradingrole = t2.tradingrole
                       and t1.hedgeflag = t2.hedgeflag
                       and t1.settlementgroupid = t3.settlementgroupid
                       and t1.instrumentid = t3.instrumentid
                       and t3.ProductClass = '2'
                       and t1.tradingday = %s
                       and t1.settlementgroupid = %s
                       and t1.settlementid = %s
                    ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                    transfee = VALUES(transfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

    # 插入t_clienttransfee表中
    sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee, OrderSysID, MinFee, MaxFee
             )select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                t1.accountid,t3.productgroupid,t3.productid,t3.underlyinginstrid,t1.instrumentid,
                t1.tradeid,t1.direction,t1.tradingrole,t1.hedgeflag,t1.offsetflag,t1.volume,t1.price,
                case
                        when t1.offsetflag = '0' or
                              t1.offsetflag = '2' then
                               t2.openfeeratio
                        when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                               t2.closetodayfeeratio
                end as transfeeratio,
                t2.valuemode,
                if(t2.valuemode='2',
                           round((case when t1.offsetflag = '0' or
                                       t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end),
                               2) * t1.volume ,
                           round((case
                                       when t1.offsetflag = '0' or
                                        t1.offsetflag = '2' then
                                        t2.openfeeratio
                                       when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                        t2.closetodayfeeratio
                               end) * t1.price * t3.volumemultiple,
                               2) * t1.volume ) as transfee,
                                               t1.OrderSysID,
                                               '0' as Minfee,
                                               '0' as MaxFee
                       from dbclear.t_trade t1,dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                       where t1.TradingDay = t2.TradingDay
                       and t1.SettlementID = t2.SettlementID
                       and t1.settlementgroupid = t2.settlementgroupid
                       and t2.participantid = t1.participantid
                       and t2.clientid = t1.clientid
                       and t1.instrumentid = t2.instrumentid
                       and t1.tradingrole = t2.tradingrole
                       and t1.hedgeflag = t2.hedgeflag
                       and t1.settlementgroupid = t3.settlementgroupid
                       and t1.instrumentid = t3.instrumentid
                       and t3.ProductClass = '2'
                       and t1.tradingday = %s
                       and t1.settlementgroupid = %s
                       and t1.settlementid = %s
                      ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                        transfee = VALUES(transfee)"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

    # 持仓权利金
    logger.info("[Calculate Options PositionPremium] is processing......")
    # 插入t_clientpositionpremium表中
    sql = """INSERT INTO dbclear.t_clientpositionpremium
                        (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,InstrumentID,Volume,UserID,Premium) 
                        SELECT
                            TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,InstrumentID,sum(Volume),UserID,sum( Premium ) 
                        FROM
                            (
                            SELECT
                                t1.TradingDay,t1.SettlementGroupID,t1.SettlementID,t1.Direction,t1.ParticipantID,t1.ClientID,t1.AccountID,
                                t1.InstrumentID,if (t1.OffsetFlag = '0',t1.Volume, -1 * t1.Volume ) as Volume,t1.UserID,
                                ROUND( IF ( t1.Direction = '0', - 1 * Price * t2.VolumeMultiple * t2.UnderlyingMultiple, Price * t2.VolumeMultiple * t2.UnderlyingMultiple) , 2 ) * t1.Volume AS Premium 
                            FROM
                                dbclear.t_trade t1,siminfo.t_instrument t2 
                            WHERE
                                 t1.settlementgroupid = t2.settlementgroupid 
                                AND t1.instrumentid = t2.instrumentid 
                                and t2.ProductClass = '2'
                                AND t1.tradingday = %s 
                                AND t1.settlementgroupid = %s 
                                AND t1.settlementid = %s
                            ) t 
                          GROUP BY TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,			
                            InstrumentID,UserID"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

    # 持仓保证金
    logger.info("[Calculate Options PositionMargin] is processing......")
    # 插入t_clientpositionmargin表中
    # （一）期权合约结算价×期权合约相对应的期货交易单位＋标的期货合约交易保证金－（１／２）×期权虚职额；
    # （二）期权合约结算价×期权合约相对应的期货交易单位＋（１／２）×标的期货合约交易保证金。
    # 看涨期权的虚值额＝Ｍａｘ（期权合约行权价格－标的期货合约结算价，０）×交易单位；
    # 看跌期权的虚值额＝Ｍａｘ（标的期货合约结算价－期权合约行权价格，０）×交易单位。
    sql = """insert into dbclear.t_clientpositionmargin(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,TradingRole,HedgeFlag,PosiDirection,Position,MarginRatio,ValueMode,SettlementPrice,PositionMargin
                )SELECT t1.tradingday,
                        t1.settlementgroupid,
                        t1.settlementid,
                        t1.participantid,
                        t1.clientid,
                        t2.AccountID,
                        t4.productgroupid,
                        t4.productid,
                        t4.underlyinginstrid,
                        t1.instrumentid,
                        t1.tradingrole,
                        t1.hedgeflag,
                        t1.posidirection,
                        t1.position,
                        if (t1.posidirection = '3',t5.ShortMarginRatio,0) as MarginRatio,
                        t5.ValueMode,
                        t3.SettlementPrice,
                        if (t1.posidirection = '3', GREATEST(
                        round(t3.SettlementPrice * t4.VolumeMultiple * t4.UnderlyingMultiple + 
                                        if(t5.ValueMode = '1', 
                                                t5.ShortMarginRatio * (t1.Position + t1.YdPosition) * t4.underlyvolumemultiple * t4.SettlementPrice,
                                                t5.ShortMarginRatio * (t1.Position + t1.YdPosition) * t4.underlyvolumemultiple 
                                                ) -
                                        (1/2) * if(t4.OptionsType = '1', 
                                                                GREATEST(t4.StrikePrice - t4.SettlementPrice,0) * t4.VolumeMultiple * t4.UnderlyingMultiple,
                                                                GREATEST(t4.SettlementPrice - t4.StrikePrice,0)), 2) * t4.VolumeMultiple * t4.UnderlyingMultiple,
                        round(t3.SettlementPrice * t4.VolumeMultiple * t4.UnderlyingMultiple + 
                                            (1/2) * if(t5.ValueMode = '1', 
                                                t5.ShortMarginRatio * (t1.Position + t1.YdPosition) * t4.underlyvolumemultiple * t4.SettlementPrice,
                                                t5.ShortMarginRatio * (t1.Position + t1.YdPosition) * t4.underlyvolumemultiple) , 2)
                       ), 0) as positionmargin
                    FROM
                    ( SELECT t1.*, t2.tradingrole FROM dbclear.t_clientposition t1, siminfo.t_client t2 WHERE t1.clientid = t2.clientid and t2.SettlementGroupID = %s) t1,
                    siminfo.t_PartRoleAccount t2,
                    dbclear.t_marketdata t3,
                    (select t.*, t1.volumemultiple as underlyvolumemultiple,t2.SettlementPrice
                        from siminfo.t_instrument t left join siminfo.t_instrument t1 on t.UnderlyingInstrID = t1.InstrumentID and t.SettlementGroupID = t1.SettlementGroupID 
                        left join dbclear.t_marketdata t2 on t2.TradingDay = %s and t2.SettlementID = %s and t.SettlementGroupID = t2.SettlementGroupID and t.InstrumentID = t2.InstrumentID
                        where t.ProductClass = '2' and t.SettlementGroupID = %s) t4,
                    siminfo.t_marginratedetail t5
                    WHERE t2.TradingRole = t1.TradingRole
                            and t2.SettlementGroupID = t1.SettlementGroupID
                            and t2.ParticipantID = t1.ParticipantID
                            AND t1.tradingday = t3.tradingday 
                            and t1.instrumentid = t5.InstrumentID
                            AND t1.instrumentid = t4.instrumentid 
                            and t1.InstrumentID = t3.InstrumentID
                            AND t1.settlementid = t3.settlementid 
                            AND t1.settlementgroupid = t3.settlementgroupid 
                            AND t1.settlementgroupid = t4.settlementgroupid 
                            and t1.SettlementGroupID = t5.SettlementGroupID
                            and t4.ProductClass = '2'
                            AND ( t1.posidirection = '2' OR t1.posidirection = '3' )
                            and t1.tradingday = %s
                            and t1.settlementgroupid = %s
                            and t1.settlementid = %s"""
    cursor.execute(sql, (settlement_group_id, current_trading_day, settlement_id, settlement_group_id,
                         current_trading_day, settlement_group_id, settlement_id))


def calc_future_posdtl(logger, cursor, current_trading_day, settlement_group_id, settlement_id, exchange_id):
    logger.info("[calc_future_posdtl ] begin")
    sql = """DELETE  FROM dbclear.t_FuturePositionDtl WHERE tradingday = %s AND settlementgroupid= %s AND settlementid = %s"""
    cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

    # 结算正在进行的赛事数据
    position_dtls = []
    direction_pairs = [["0", "1"], ["1", "0"]]
    for direction_pair in direction_pairs:
        sql = """SELECT t.ClientID,t.InstrumentID,t.HedgeFlag,t.Direction,t.OpenDate,t.TradeID,t.Volume,t.OpenPrice,t.TradeType,t.ParticipantID, t.CloseProfitByDate,t.CloseProfitByTrade,t.PositionProfitByDate,t.PositionProfitByTrade,t.Margin,t.ExchMargin,t.MarginRateByMoney,t.MarginRateByVolume,t.LastSettlementPrice,t.SettlementPrice,t.CloseVolume,t.CloseAmount
                            FROM (SELECT ClientID,
                                  InstrumentID,
                                  HedgeFlag,
                                  Direction,
                                  OpenDate,
                                  TradeID,
                                  Volume,
                                  OpenPrice,
                                  TradeType,
                                  ParticipantID,
                                  CloseProfitByDate,
                                  CloseProfitByTrade,
                                  PositionProfitByDate,
                                  PositionProfitByTrade,
                                  Margin,
                                  ExchMargin,
                                  MarginRateByMoney,
                                  MarginRateByVolume,
                                  LastSettlementPrice,
                                  SettlementPrice,
                                  CloseVolume,
                                  CloseAmount
                                  FROM siminfo.t_FuturePositionDtl
                                  WHERE tradingday = %s AND settlementgroupid = %s AND direction = %s
                                  UNION ALL
                                SELECT ClientID,
                                      InstrumentID,
                                      HedgeFlag,
                                      Direction,
                                      TradingDay AS OpenDate,
                                      TradeID,
                                      Volume,
                                      Price AS OpenPrice,
                                      TradeType,
                                      ParticipantID,
                                      0 AS CloseProfitByDate,
                                      0 AS CloseProfitByTrade,
                                      0 AS PositionProfitByDate,
                                      0 AS PositionProfitByTrade,
                                      0 AS Margin,
                                      0 AS ExchMargin,
                                      0 AS MarginRateByMonfutureey,
                                      0 AS MarginRateByVolume,
                                      0 AS LastSettlementPrice,
                                      0 AS SettlementPrice,
                                      0 AS CloseVolume,
                                      0 AS CloseAmount
                                    FROM
                                      dbclear.t_trade 
                                      WHERE tradingday = %s AND settlementgroupid = %s AND settlementid = %s AND direction = %s AND offsetflag = '0' ) t
                            ORDER BY t.ClientID, t.InstrumentID, t.HedgeFlag, t.OpenDate, t.TradeID"""
        cursor.execute(sql, (
            current_trading_day, settlement_group_id, direction_pair[0], current_trading_day, settlement_group_id,
            settlement_id, direction_pair[0],))
        open_positions = cursor.fetchall()

        sql = """SELECT t.ClientID,t.InstrumentID,
                      t.HedgeFlag,
                      t.Direction,
                      t.TradeID,
                      t.Volume AS CloseVolume,
                      t.Price AS ClosePrice,
                      t1.VolumeMultiple AS VolumeMultiple
                      FROM dbclear.t_trade t, siminfo.t_instrument t1 
                      WHERE t.instrumentid = t1.instrumentid AND t.settlementgroupid = t1.settlementgroupid 
                      AND t.tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s AND t.direction = %s AND t.offsetflag = '1'
                      ORDER BY t.ClientID, t.InstrumentID, t.HedgeFlag, t.TradeID"""
        cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id, direction_pair[1],))
        close_positions = cursor.fetchall()

        open_positions_array = []
        for open_position in open_positions:
            open_positions_array.append(list(open_position))

        open_index = 0
        for close_position in close_positions:
            client_id = str(close_position[0])
            instrument_id = str(close_position[1])
            close_volume = int(str(close_position[5]))
            close_price = float(str(close_position[6]))
            volume_multiple = int(str(close_position[7]))

            ranges = range(open_index, len(open_positions_array))
            for idx in ranges:
                open_index = idx
                open_position = open_positions_array[idx]
                if client_id != str(open_position[0]) or instrument_id != str(open_position[1]):
                    continue
                open_volume = int(str(open_position[6]))
                open_price = float(str(open_position[7]))
                total_close_profit = float(str(open_position[10]))
                total_close_volume = int(str(open_position[20]))
                total_close_amount = float(str(open_position[21]))

                curr_close_volume = 0
                if open_volume > 0:
                    if open_volume >= close_volume:
                        curr_close_volume = close_volume
                        open_volume -= close_volume
                        close_volume = 0
                    else:
                        curr_close_volume = open_volume
                        close_volume -= open_volume
                        open_volume = 0

                total_close_volume += curr_close_volume
                total_close_amount += round(close_price * curr_close_volume * volume_multiple, 2)
                if direction_pair[0] == '0':
                    total_close_profit += round((close_price - open_price) * curr_close_volume * volume_multiple, 2)
                else:
                    total_close_profit += round((open_price - close_price) * curr_close_volume * volume_multiple, 2)

                open_position[6] = str(open_volume)
                open_position[10] = str(total_close_profit)
                open_position[20] = str(total_close_volume)
                open_position[21] = str(total_close_amount)

                if open_volume == 0:
                    open_index = idx + 1

                if close_volume == 0:
                    break

        position_dtls.append(open_positions_array)

    sql = """INSERT INTO dbclear.t_FuturePositionDtl(TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,
                                                      Volume,OpenPrice,TradeType,CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,SettlementPrice,CloseVolume,CloseAmount)
                                                    VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    for position_array in position_dtls:
        sql_params = []
        for position in position_array:
            sql_params.append((current_trading_day, settlement_group_id, settlement_id, str(position[1]),
                               str(position[9]), str(position[0]),
                               str(position[2]), str(position[3]), str(position[4]), str(position[5]),
                               str(position[6]), str(position[7]), str(position[8]), "", exchange_id,
                               str(position[10]), str(position[11]), str(position[12]), str(position[13]),
                               str(position[14]), str(position[15]),
                               str(position[16]), str(position[17]), str(position[18]), str(position[19]),
                               str(position[20]), str(position[21])))
        if len(sql_params) > 0:
            cursor.executemany(sql, sql_params)
    logger.info("[calc_future_posdtl] end")


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_future(context, conf))


if __name__ == "__main__":
    main()
