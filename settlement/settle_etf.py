# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_etf(context, conf):
    result_code = 0
    logger = log.get_logger(category="Settleetf")

    settlement_group_id = conf.get("settlementGroupId")
    settlement_id = conf.get("settlementId")
    stock_settle = conf.get("stock_settle")

    logger.info("[settle etf %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
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
            logger.error("[settle etf] Error: There is no data for %s-%s." % (settlement_group_id, settlement_id))
            result_code = -1
        elif row[3] != '0':
            logger.error("[settle etf] Error: Settlement for %s-%s has done." % (settlement_group_id, settlement_id))
            result_code = -1
        else:
            # 更新标的收盘价
            logger.info("[calculate settlement price] is processing......")
            sql = """UPDATE dbclear.t_marketdata t1,
                                    (
                                    SELECT
                    t.instrumentid,
                    t.UnderlyingInstrID,
                    t2.ClosePrice 
                    FROM
                    siminfo.t_instrument t
                    LEFT JOIN (select * from dbclear.t_marketdata where tradingday = %s and settlementgroupid = %s and settlementid = %s) t2 ON (t.UnderlyingInstrID = t2.InstrumentID)
                    where t.settlementgroupid = %s 
                                        ) t2 
                                        SET t1.UnderlyingClosePx = t2.ClosePrice 
                                    WHERE
                                        t1.InstrumentID = t2.instrumentid 
                                        AND t1.TradingDay = %s
                                        AND t1.SettlementID = %s
                                        AND t1.SettlementGroupID = %s """
            cursor.execute(sql, (current_trading_day, stock_settle, settlement_id, settlement_group_id, current_trading_day, settlement_id, settlement_group_id))

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
            logger.info("[Move DelivPosition] is processing......")
            sql = "delete from dbclear.t_delivinstrument where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            # 1）插入到t_delivinstrument表
            sql = """insert into dbclear.t_delivinstrument(TradingDay, SettlementGroupID, SettlementID, InstrumentID
                                               )select %s, t.SettlementGroupID, %s, t.instrumentid
                                               from siminfo.t_instrumentproperty t
                                               where t.settlementgroupid = %s and t.startdelivdate <= %s"""
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
            # 4) 计算行权盈亏
            sql = """INSERT INTO dbclear.t_clientdelivprofit(TradingDay, SettlementGroupID, SettlementID, ParticipantID, AccountID, ClientID, HedgeFlag, InstrumentID, PosiDirection, POSITION, OptionsType, VolumeMultiple, UnderlyingMultiple, StrikePrice, SettlementPrice, Profit)
                                                SELECT 
                                                  t1.tradingday,
                                                  t1.settlementgroupid,
                                                  t1.settlementid,
                                                  t1.participantid,
                                                  t2.accountid,
                                                  t1.clientid,
                                                  t1.hedgeflag,
                                                  t1.instrumentid,
                                                  t1.posidirection,
                                                  t1.position,
                                                  t3.optionstype,
                                                  t3.volumemultiple,
                                                  t3.underlyingmultiple,
                                                  t3.strikeprice,
                                                  t3.settlementprice,
                                                  CASE
                                                    WHEN t3.optionstype = '1' 
                                                    THEN IF(t1.posidirection = '2', 1, - 1) * (
                                                      t3.settlementprice - t3.strikeprice
                                                    ) * t1.position * t3.volumemultiple * t3.underlyingmultiple 
                                                    WHEN t3.optionstype = '2' 
                                                    THEN IF(t1.posidirection = '2', - 1, 1) * (
                                                      t3.settlementprice - t3.strikeprice
                                                    ) * t1.position * t3.volumemultiple * t3.underlyingmultiple 
                                                    ELSE 0 
                                                  END AS delivprofit 
                                                FROM
                                                  (SELECT 
                                                    t1.*,
                                                    t2.tradingrole 
                                                  FROM
                                                    dbclear.t_clientdelivposition t1,
                                                    siminfo.t_client t2 
                                                  WHERE t1.clientid = t2.clientid) t1,
                                                  siminfo.t_PartRoleAccount t2,
                                                  (SELECT 
                                                    t2.tradingday,
                                                    t1.settlementgroupid,
                                                    t2.settlementid,
                                                    t1.instrumentid,
                                                    t1.strikeprice,
                                                    t1.optionstype,
                                                    t1.volumemultiple,
                                                    t1.underlyingmultiple,
                                                    t2.UnderlyingClosePx as settlementprice 
                                                  FROM
                                                    siminfo.t_instrument t1,
                                                    dbclear.t_marketdata t2 
                                                  WHERE t1.settlementgroupid = %s
                                                    AND t2.tradingday = %s
                                                    AND t2.settlementid = %s
                                                    AND (
                                                      (
                                                        t1.optionstype = '1' 
                                                        AND t1.strikeprice < t2.settlementprice
                                                      ) 
                                                      OR (
                                                        t1.optionstype = '2' 
                                                        AND t1.strikeprice > t2.settlementprice
                                                      )
                                                    ) 
                                                    AND t1.SettlementGroupID = t2.SettlementGroupID 
                                                    AND t1.instrumentid = t2.instrumentid) t3 
                                                WHERE t2.TradingRole = t1.TradingRole 
                                                  AND t2.SettlementGroupID = t1.SettlementGroupID 
                                                  AND t2.ParticipantID = t1.ParticipantID 
                                                  AND t1.instrumentid = t3.instrumentid 
                                                  AND t1.tradingday = t3.tradingday 
                                                  AND t1.settlementgroupid = t3.settlementgroupid 
                                                  AND t1.settlementid = t3.settlementid 
                                                  AND (
                                                    t1.posidirection = '2' 
                                                    OR t1.posidirection = '3'
                                                  ) 
                                                  AND t1.tradingday = %s
                                                  AND t1.settlementgroupid = %s
                                                  AND t1.settlementid = %s
                                          """
            cursor.execute(sql, (settlement_group_id, current_trading_day, settlement_id, current_trading_day, settlement_group_id, settlement_id,))

            # 交割手续费
            sql = """"""
            # 交易手续费
            logger.info("[Calculate TransFee] is processing......")
            sql = "delete from dbclear.t_clienttransfee where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            # 插入t_clienttransfee表中(CloseYesterdayFeeRatio存放的是佣金)
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
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume, 2),
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t1.price * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume ,
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
                                 when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                    t2.closetodayfeeratio
                             end as transfeeratio,
                             t2.valuemode,
                             if(t2.valuemode='2',
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume, 2),
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t1.price * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume ,
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
                                 when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                    t2.closetodayfeeratio
                             end as transfeeratio,
                             t2.valuemode,
                             if(t2.valuemode='2',
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume, 2),
                                            round(((case
                                                            when t1.offsetflag = '0' or
                                                                     t1.offsetflag = '2' then
                                                             t2.openfeeratio
                                                            when t1.offsetflag = '3' or t1.offsetflag = '1' or  t1.offsetflag = '4' then
                                                             t2.closetodayfeeratio
                                                        end) * t1.price * t3.volumemultiple + t2.CloseYesterdayFeeRatio) * t1.volume ,
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
                                and t1.tradingday = %s
                                and t1.settlementgroupid = %s
                                and t1.settlementid = %s
                                ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                        transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 持仓保证金
            # 认购期权虚值=行权价-50ETF（前）收盘价（如果差值为负则虚值为零）
            # 认沽期权虚值=50ETF（前）收盘价-行权价（如果差值为负则虚值为零）
            # 认购期权义务仓维持保证金＝[合约结算价+Max（12%×合约标的收盘价-认购期权虚值，7%×合约标的收盘价）]×合约单位
            # MarginRatio = [SettlementPrice + Max(0.12 * UnderlyingClosePx - Max(strikeprice - UnderlyingClosePx, 0) , 0.07 * UnderlyingClosePx)] * underlyingmultiple
            # 认沽期权义务仓维持保证金＝Min[合约结算价 +Max（12%×合标的收盘价-认沽期权虚值，7%×行权价格），行权价格]×合约单位
            # MarginRatio = Min[SettlementPrice + Max(0.12 * UnderlyingClosePx - Max(UnderlyingClosePx - strikeprice,0), 0.07 * strikeprice), strikeprice] * underlyingmultiple
            logger.info("[Calculate PositionMargin] is processing......")
            sql = "delete from dbclear.t_clientpositionmargin where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
            # 插入t_clientpositionmargin表中
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
                                if (t1.posidirection = '3',if ( t4.OptionsType = '1',
                                (t3.SettlementPrice + greatest(0.12 * t3.UnderlyingClosePx - greatest(t4.strikeprice - t3.UnderlyingClosePx, 0) , 0.07 * t3.UnderlyingClosePx)) * t4.underlyingmultiple ,
                                LEAST(t3.SettlementPrice + greatest(0.12 * t3.UnderlyingClosePx - greatest(t3.UnderlyingClosePx - t4.strikeprice,0), 0.07 * t4.strikeprice), t4.strikeprice) * t4.underlyingmultiple ),0) AS MarginRatio ,
                                '2' as valuemode,
                                t3.SettlementPrice,
                                if (t1.posidirection = '3',if ( t4.OptionsType = '1',
                                (t3.SettlementPrice + greatest(0.12 * t3.UnderlyingClosePx - greatest(t4.strikeprice - t3.UnderlyingClosePx, 0) , 0.07 * t3.UnderlyingClosePx)) * t4.underlyingmultiple ,
                                LEAST(t3.SettlementPrice + greatest(0.12 * t3.UnderlyingClosePx - greatest(t3.UnderlyingClosePx - t4.strikeprice,0), 0.07 * t4.strikeprice), t4.strikeprice) * t4.underlyingmultiple ),0) * (t1.position + t1.YdPosition) AS positionmargin 
                            FROM
                                ( SELECT t1.*, t2.tradingrole FROM dbclear.t_clientposition t1, siminfo.t_client t2 WHERE t1.clientid = t2.clientid and t1.settlementgroupid = t2.settlementgroupid) t1,
                                siminfo.t_PartRoleAccount t2,
                                dbclear.t_marketdata t3,
                                siminfo.t_instrument t4 
                            WHERE t2.TradingRole = t1.TradingRole
                                and t2.SettlementGroupID = t1.SettlementGroupID
                                and t2.ParticipantID = t1.ParticipantID
                                and t1.instrumentid = t3.instrumentid 
                                AND t1.tradingday = t3.tradingday 
                                AND t1.settlementgroupid = t3.settlementgroupid 
                                AND t1.settlementid = t3.settlementid 
                                AND t1.settlementgroupid = t4.settlementgroupid 
                                AND t1.instrumentid = t4.instrumentid 
                                AND ( t1.posidirection = '2' OR t1.posidirection = '3' )
                                and t1.tradingday = %s
                                and t1.settlementgroupid = %s
                                and t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 持仓权利金
            logger.info("[Calculate PositionPremium] is processing......")
            sql = "delete from dbclear.t_clientpositionpremium where settlementgroupid = %s and settlementid = %s and tradingday = %s "
            cursor.execute(sql, (settlement_group_id, settlement_id, current_trading_day))
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
                            ROUND( IF (t1.Direction = '0', - 1 * Price * t2.UnderlyingMultiple, Price * t2.UnderlyingMultiple) * t1.Volume , 2 ) AS Premium 
                        FROM
                            dbclear.t_trade t1,siminfo.t_instrument t2 
                        WHERE
                             t1.settlementgroupid = t2.settlementgroupid 
                            AND t1.instrumentid = t2.instrumentid 
                            AND t1.tradingday = %s 
                            AND t1.settlementgroupid = %s 
                            AND t1.settlementid = %s
                        ) t 
                      GROUP BY TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,			
                        InstrumentID,UserID"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 客户持仓
            logger.info("[update client position]......")
            sql = """UPDATE dbclear.t_clientposition t,
                            (
                                SELECT
                                    t.tradingday,
                                    t.settlementgroupid,
                                    t.settlementid,
                                    t.participantid,
                                    t.clientid,
                                    t.accountid,
                                    t.transfee,
                                    t1.Premium,
                                    t2.positionmargin,
                                    t.InstrumentID 
                                FROM
                                    (
                                    SELECT
                                        t.tradingday,
                                        t.settlementgroupid,
                                        t.settlementid,
                                        t.participantid,
                                        t.clientid,
                                        t.accountid,
                                        sum( t.transfee ) AS transfee,
                                        t.InstrumentID 
                                    FROM
                                        dbclear.t_clienttransfee t 
                                    WHERE
                                        t.tradingday = %s
                                        AND t.settlementgroupid = %s 
                                        AND t.settlementid = %s
                                    GROUP BY
                                        t.tradingday,
                                        t.settlementgroupid,
                                        t.settlementid,
                                        t.participantid,
                                        t.clientid,
                                        t.accountid,
                                        t.InstrumentID 
                                    ) t,
                                    dbclear.t_clientpositionpremium t1,
                                    dbclear.t_clientpositionmargin t2 
                                WHERE
                                    t.TradingDay = t1.TradingDay 
                                    AND t.TradingDay = t2.TradingDay 
                                    AND t.SettlementGroupID = t1.SettlementGroupID 
                                    AND t.SettlementGroupID = t2.SettlementGroupID 
                                    AND t.SettlementID = t1.SettlementID 
                                    AND t.SettlementID = t2.SettlementID 
                                    AND t.ParticipantID = t1.ParticipantID 
                                    AND t.ParticipantID = t2.ParticipantID 
                                    AND t.ClientID = t1.ClientID 
                                    AND t.ClientID = t2.ClientID 
                                    AND t.accountid = t1.AccountID 
                                    AND t.accountid = t2.AccountID 
                                ) t1 
                                SET t.PositionCost = abs( t1.Premium ) + t1.transfee 
                            WHERE
                                t.InstrumentID = t1.InstrumentID 
                                AND t.TradingDay = t1.TradingDay 
                                AND t.SettlementGroupID = t1.SettlementGroupID 
                                AND t.SettlementID = t1.SettlementID 
                                AND t.ClientID = t1.ClientID 
                                AND t.ParticipantID = t1.ParticipantID 
                                AND t.tradingday = %s 
                                AND t.settlementgroupid = %s 
                                AND t.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id,
                                 current_trading_day, settlement_group_id, settlement_id))
            # 客户资金
            logger.info("[Calculate ClientFund] is processing......")
            # 1）更新transfee
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,sum(t.transfee) as transfee,0,0,0,0,0
                                            from dbclear.t_clienttransfee t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                            group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                            ON DUPLICATE KEY UPDATE dbclear.t_clientfund.transfee = values(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 2）更新delivfee
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                          (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,sum(t.delivfee) as delivfee,0,0,0,0
                                            from dbclear.t_clientdelivfee t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                            group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                            ON DUPLICATE KEY UPDATE t_clientfund.delivfee = values(delivfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 3）更新profit
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                           (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,0,sum(t.profit) as profit,0,0
                                           from dbclear.t_clientdelivprofit t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                           group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                           ON DUPLICATE KEY UPDATE dbclear.t_clientfund.profit = values(profit)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 4）更新premium
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                       (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,0,0,sum( t.Premium ) AS available,0
                                     from dbclear.t_clientpositionpremium t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                     group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid)
                                      ON DUPLICATE KEY UPDATE dbclear.t_clientfund.available = values(available)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 5）更新positionmargin
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                          (select t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid,0,0,sum(t.positionmargin) as positionmargin,0,0,0
                                          from dbclear.t_clientpositionmargin t where t.tradingday = %s and t.settlementgroupid = %s and t.settlementid = %s
                                          group by t.tradingday,t.settlementgroupid,t.settlementid,t.participantid,t.clientid,t.accountid) 
                                          ON DUPLICATE KEY UPDATE dbclear.t_clientfund.positionmargin = values(positionmargin)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            # 6）更新stockvalue
            sql = """insert into dbclear.t_clientfund (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID,TransFee,DelivFee,PositionMargin,Profit,available,StockValue)
                                          (SELECT  t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t2.accountid, t1.clientid, 0 AS transfee, 0 AS delivfee, 0 AS positionmargin, 0 AS profit, 0 AS available,
                                                          ROUND(SUM(
                                                            CASE
                                                              WHEN t1.posidirection = '2' 
                                                              THEN t1.position * t3.settlementprice * t4.underlyingmultiple 
                                                              WHEN t1.posidirection = '3' 
                                                              THEN - 1 * t1.position * t3.settlementprice * t4.underlyingmultiple 
                                                              ELSE 0 
                                                            END
                                                          ), 2) AS stockvalue 
                                                        FROM
                                                          (SELECT 
                                                            t1.*,
                                                            t2.tradingrole 
                                                          FROM
                                                            dbclear.t_clientposition t1,
                                                            siminfo.t_client t2 
                                                          WHERE t1.clientid = t2.clientid) t1,
                                                          siminfo.t_PartRoleAccount t2,
                                                          dbclear.t_marketdata t3,
                                                          siminfo.t_instrument t4 
                                                        WHERE t2.TradingRole = t1.TradingRole 
                                                          AND t2.SettlementGroupID = t1.SettlementGroupID 
                                                          AND t2.ParticipantID = t1.ParticipantID 
                                                          AND t1.instrumentid = t3.instrumentid 
                                                          AND t1.tradingday = t3.tradingday 
                                                          AND t1.settlementgroupid = t3.settlementgroupid 
                                                          AND t1.settlementid = t3.settlementid 
                                                          AND t1.settlementgroupid = t4.settlementgroupid 
                                                          AND t1.instrumentid = t4.instrumentid 
                                                          AND (
                                                            t1.posidirection = '2' 
                                                            OR t1.posidirection = '3'
                                                          ) 
                                                          AND t1.tradingday = %s
                                                          AND t1.settlementgroupid = %s
                                                          AND t1.settlementid = %s
                                                        GROUP BY t1.tradingday,
                                                          t1.settlementgroupid,
                                                          t1.settlementid,
                                                          t1.participantid,
                                                          t2.accountid,
                                                          t1.clientid) 
                                          ON DUPLICATE KEY UPDATE dbclear.t_clientfund.stockvalue = values(stockvalue)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 更新结算状态
            logger.info("[update settlement status] is processing......")
            sql = """UPDATE dbclear.t_settlement SET settlementstatus = '1' 
                                    WHERE tradingday = %s AND settlementgroupid = %s AND settlementid = %s AND settlementstatus = '0'"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle etf] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle etf] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_etf(context, conf))


if __name__ == "__main__":
    main()
