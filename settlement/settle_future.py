# -*- coding: UTF-8 -*-
"""
缺少
t_clientdelivfee
t_ClientPositionProfit
t_delivinstrument
t_ClientProfit
t_clientPositionProfit
t_partfund
t_clientprofit
t_partdelivposition
t_clientdelivposition
"""
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
            logger.info("[Move DelivPosition]......")
            sql = "delete from dbclear.t_delivinstrument where settlementgroupid = %s and settlementid = %"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 1）插入到t_delivinstrument表，目前startdelivdate为999999
            sql = """insert into dbclear.t_delivinstrument(TradingDay, SettlementGroupID, SettlementID, InstrumentID)
                    select %s, t.SettlementGroupID, %s, t.instrumentid
                    from siminfo.t_instrumentproperty t
                    where t.settlementgroupid = %s and t.startdelivdate <= %s"""
            cursor.execute(sql, (current_trading_day, settlement_id, settlement_group_id, next_trading_day))
            # 2）插入到t_partdelivposition
            sql = """insert into dbclear.t_partdelivposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,
                    YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,InstrumentID,ParticipantID,TradingRole)
                    select TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,
                    LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,InstrumentID,ParticipantID,TradingRole from dbclear.t_partposition 
                     where tradingday = %s and settlementgroupid = %s and settlementid = %s
                       and instrumentid in
                           (select t.instrumentid
                              from dbclear.t_delivinstrument t
                             where t.tradingday = %s
                                and t.settlementgroupid = %s
                                and t.settlementid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 3）插入到t_clientdelivposition
            sql = """insert into dbclear.t_clientdelivposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,
                      PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,
                      BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,
                      LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID)
                    select TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,
                    LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,
                    YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,
                    InstrumentID,ParticipantID,ClientID from dbclear.t_clientposition
                     where tradingday = %s
                       and settlementgroupid = %s
                       and settlementid = %s
                       and instrumentid in       
                           (select t.instrumentid
                              from dbclear.t_delivinstrument t
                             where t.tradingday = %s
                                and t.settlementgroupid = %s
                                and t.settlementid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 4）删除t_partposition持仓数据
            sql = """delete from dbclear.t_partposition 
                         where tradingday = %s
                           and settlementgroupid = %s
                           and settlementid = %s
                           and instrumentid in
                               (select t.instrumentid
                                  from dbclear.t_delivinstrument t
                                 where t.tradingday = %s
                                    and t.settlementgroupid = %s
                                    and t.settlementid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 5) 删除t_clientposition
            sql = """delete from dbclear.t_clientposition
                         where tradingday = %s
                           and settlementgroupid = %s
                           and settlementid = %s
                           and instrumentid in
                               (select t.instrumentid
                                  from dbclear.t_delivinstrument t
                                 where t.tradingday = %s
                                    and t.settlementgroupid = %s
                                    and t.settlementid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 交割手续费
            logger.info("[Calculate DelivFee]......")
            sql = "delete from dbclear.t_clientdelivfee where settlementgroupid = %s and settlementid = %s"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 插入t_clientdelivfee表中
            sql = """insert into dbclear.t_clientdelivfee(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,Position,DelivPrice,DelivFeeRatio,ValueMode,DelivFee)
                        select t1.tradingday,
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
                               t4.settlementprice as delivprcie,
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
                           (select t1.settlementgroupid,
                                   t1.participantid,
                                   t1.clientid,
                                   t1.accountid,
                                   t2.instrumentid,
                                   ifnull(t4.delivfeeratio, ifnull(t3.delivfeeratio, t2.delivfeeratio)) as delivfeeratio,
                                   ifnull(t4.valuemode, ifnull(t3.valuemode, t2.valuemode)) as valuemode
                              from (select t3.settlementgroupid,
                                           t2.participantid,
                                           t1.clientid,
                                           t3.accountid
                                      from siminfo.t_client t1, siminfo.t_partclient t2, siminfo.t_partroleaccount t3
                                     where t1.clientid = t2.clientid
                                       and t2.participantid = t3.participantid
                                       and t3.settlementgroupid = %s) t1
                              left join siminfo.t_delivfeeratedetail t2
                                on (t1.settlementgroupid = t2.settlementgroupid and
                                   t1.settlementgroupid = %s and
                                   t2.participantid = '00000000' and
                                   t2.clientid = '00000000')
                              left join siminfo.t_delivfeeratedetail t3
                                on (t1.settlementgroupid = t3.settlementgroupid and
                                   t1.settlementgroupid = %s and
                                   t1.participantid = t3.participantid and
                                   t3.clientid = '00000000')
                              left join siminfo.t_delivfeeratedetail t4
                                on (t1.settlementgroupid = t4.settlementgroupid and
                                   t1.settlementgroupid = %s and
                                   t1.participantid = t4.participantid and
                                   t1.clientid = t4.clientid)) t2,
                           siminfo.t_instrument t3,
                           dbclear.t_marketdata t4
                        where t1.settlemesettlementgroupidntgroupid = t2.settlementgroupid
                        and t1.participantid = t2.participantid
                        and t1.clientid = t2.clientid
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
                                 settlement_group_id, settlement_group_id, settlement_group_id, settlement_group_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 交易手续费
            logger.info("[Calculate TransFee]......")
            sql = "delete from dbclear.t_clienttransfee where settlementgroupid = %s and settlementid = %s"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 插入t_clienttransfee表中
            sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee)
                      select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
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
                                    end) * t1.volume * t3.volumemultiple,
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
                                    2)) as transfee
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
                        and t1.tradingday = %s
                        and t1.settlementgroupid = %s
                        and t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee)
                      select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
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
                                                end) * t1.volume * t3.volumemultiple,
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
                                                2)) as transfee
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
                                    and t1.tradingday = %s
                                    and t1.settlementgroupid = %s
                                    and t1.settlementid = %s
                                    ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                            transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """insert into dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, TransFee)
                                  select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
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
                                                end) * t1.volume * t3.volumemultiple,
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
                                                2)) as transfee
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
                                    and t1.tradingday = %s
                                    and t1.settlementgroupid = %s
                                    and t1.settlementid = %s
                                    ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                            transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 持仓保证金
            logger.info("[Calculate PositionMargin]......")
            sql = "delete from dbclear.t_clientpositionmargin where settlementgroupid = %s and settlementid = %s"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 插入t_clientpositionmargin表中
            sql = """insert into dbclear.t_clientpositionmargin(TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,UnderlyingInstrID,InstrumentID,TradingRole,HedgeFlag,PosiDirection,Position,MarginRatio,ValueMode,SettlementPrice,PositionMargin)
                        select t1.tradingday,t1.settlementgroupid,t1.settlementid,t1.participantid,t1.clientid,
                        t2.accountid,t4.productgroupid,t4.productid,t4.underlyinginstrid,t1.instrumentid,t1.tradingrole,
                        t1.hedgeflag,t1.posidirection,t1.position + t1.ydposition,
                        if(t1.posidirection='2',
                          t2.longmarginratio,
                          t2.shortmarginratio) as marginrate,
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
                                t1.accountid,
                                t1.clientid,
                                t2.instrumentid,
                                t2.tradingrole,
                                t2.hedgeflag,
                                ifnull(t4.longmarginratio,
                                    ifnull(t3.longmarginratio, t2.longmarginratio)) as longmarginratio,
                                ifnull(t4.shortmarginratio,
                                    ifnull(t3.shortmarginratio, t2.shortmarginratio)) as shortmarginratio,
                                ifnull(t4.valuemode, ifnull(t3.valuemode, t2.valuemode)) as valuemode
                            from (select t3.settlementgroupid,
                                        t2.participantid,
                                        t1.clientid,
                                        t1.tradingrole,
                                        t3.accountid
                                    from siminfo.t_client t1, siminfo.t_partclient t2, siminfo.t_partroleaccount t3
                                    where t1.clientid = t2.clientid
                                    and t2.participantid = t3.participantid
                                    and t1.tradingrole = t3.tradingrole
                                    and t1.settlementgroupid = t2.settlementgroupid
                                    and t1.settlementgroupid = t3.settlementgroupid
                                    and t3.settlementgroupid = %s) t1
                            left join siminfo.t_marginratedetail t2
                                on (t1.settlementgroupid = t2.settlementgroupid and
                                t1.tradingrole = t2.tradingrole and
                                t1.settlementgroupid = %s and
                                t2.participantid = '00000000' and
                                t2.clientid = '00000000')
                            left join siminfo.t_marginratedetail t3
                                on (t1.settlementgroupid = t3.settlementgroupid and
                                t1.tradingrole = t3.tradingrole and
                                t1.settlementgroupid = %s and
                                t1.participantid = t3.participantid and
                                t3.clientid = '00000000')
                            left join siminfo.t_marginratedetail t4
                                on (t1.settlementgroupid = t4.settlementgroupid and
                                t1.tradingrole = t4.tradingrole and
                                t1.settlementgroupid = %s and
                                t1.participantid = t4.participantid and
                                t1.clientid = t4.clientid)) t2,
                            dbclear.t_marketdata t3,
                            siminfo.t_instrument t4
                        where t1.participantid = t2.participantid
                        and t1.clientid = t2.clientid
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
                        and (t1.posidirection = '2' or t1.posidirection = '3')
                        and t1.tradingday = %s
                        and t1.settlementgroupid = %s
                        and t1.settlementid = %s"""
            cursor.execute(sql, (settlement_group_id, settlement_group_id, settlement_group_id, settlement_group_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 持仓盈亏
            logger.info("[Calculate PositionProfit]......")
            sql = "delete from dbclear.t_clientPositionProfit where settlementgroupid = %s and settlementid = %s"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 写入t_clientPositionProfit表中
            sql = """insert into dbclear.t_ClientPositionProfit(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, InstrumentID, HedgeFlag, PosiDirection, PositionCost, SettlementPositionCost, PositionProfit)
                           select t1.tradingday,
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
                       and t1.tradingday = %s
                       and t1.settlementgroupid = %s
                       and t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 客户资金
            logger.info("[Calculate ClientFund]......")
            # 1）更新positionmargin
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
                    (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,,.clientid,t.accountid,0,sum(t.delivfee) as delivfee,0,0,0,0
                    from dbclear.t_clientdelivfee t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                    group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                    ON DUPLICATE KEY UPDATE dbclear.t_clientfund.delivfee = values(delivfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 4）更新profit
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                    (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,0,sum(t.profit) as profit,0,0
                    from dbclear.t_clientprofit t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                    group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                    ON DUPLICATE KEY UPDATE dbclear.t_clientfund.profit = values(profit)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 会员资金
            logger.info("[Calculate PartFund]......")
            sql = "delete from dbclear.t_partfund where settlementgroupid = %s and settlementid = %s"
            cursor.execute(sql, (settlement_group_id, settlement_id))
            # 写入t_partfund表中
            sql = """insert into dbclear.t_partfund(TradingDay, SettlementGroupID, SettlementID, ParticipantID, AccountID, TransFee, DelivFee, PositionMargin, Profit)
                    select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.accountid,sum(transfee) as transfee,sum(delivfee) as delivfee,sum(positionmargin) as positionmargin,sum(profit) as profit
                    from dbclear.t_clientfund t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                    group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.accountid"""
            # 更新结算状态
            logger.info("[update settlement status]......")
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


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_future(context, conf))


if __name__ == "__main__":
    main()
