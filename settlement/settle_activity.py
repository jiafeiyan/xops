# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_activity(context, conf):
    result_code = 0
    logger = log.get_logger(category="SettleActivity")

    bench_stock_id = conf.get("BenchStockID", "sh000300")
    statistic_rank_no = conf.get("StatisticRankNo", 10)

    logger.info("[settle activity %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        # 结算正在进行的赛事数据
        sql = """SELECT activityid, termno FROM siminfo.t_activity WHERE activitystatus != '2'"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        activities = []
        for row in rows:
            activities.append((str(row[0]), int(row[1])))

        for activity_id, term_no in activities:
            # 获取当前交易日
            logger.info("[get current trading day, last trading day for activity %s]......" % activity_id)
            sql = """SELECT DISTINCT t1.tradingday, t1.lasttradingday FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2, siminfo.t_activitysettlementgroup t3
                        WHERE t1.tradesystemid = t2.tradesystemid AND t2.settlementgroupid = t3.settlementgroupid AND t3.activityid = %s"""
            cursor.execute(sql, (activity_id,))
            rows = cursor.fetchall()
            row = rows[0]

            current_trading_day = str(row[0])
            last_trading_day = str(row[1])
            logger.info("[get current trading day, last trading day for activity %s] current_trading_day = %s, last_trading_day = %s" % (activity_id, current_trading_day, last_trading_day))

            sql = """SELECT activitystatus FROM siminfo.t_activity WHERE activityid = %s AND termno = %s"""
            cursor.execute(sql, (activity_id, term_no,))
            row = cursor.fetchone()

            activity_status = str(row[0])
            if "0" == activity_status:
                sql = """DELETE FROM siminfo.t_activityinvestorevaluation WHERE activityid = %s AND termno = %s"""
                cursor.execute(sql, (activity_id, term_no,))

            # 赛事开始状态设置
            sql = """UPDATE siminfo.t_activity 
                                    SET
                                      activitystatus = 
                                      CASE
                                        WHEN begindate <= %s
                                        AND enddate > %s
                                        THEN '1' 
                                        ELSE activitystatus 
                                      END
                                    WHERE activityid = %s AND termno = %s AND activitystatus = '0'"""
            cursor.execute(sql, (current_trading_day, current_trading_day, activity_id, term_no))

            sql = """SELECT activitystatus,initialbalance,joinmode,rankingrule,activitytype FROM siminfo.t_activity WHERE activityid = %s AND termno = %s"""
            cursor.execute(sql, (activity_id, term_no))
            row = cursor.fetchone()

            if "0" == str(row[0]):
                continue

            initial_balance = str(row[1])
            join_mode = str(row[2])
            ranking_rule = str(row[3])
            activity_type = str(row[4])

            if activity_status != str(row[0]) and "1" == str(row[0]):
                sql = """UPDATE siminfo.t_activity 
                                                    SET
                                                      termno = %s
                                                    WHERE activityid = %s AND termno = %s"""
                cursor.execute(sql, (term_no + 1, activity_id, term_no))
                term_no += 1

            if activity_type == '0':
                # 默认赛事投资者数据
                logger.info("[insert default activity investor]......")
                sql = """INSERT INTO siminfo.t_activityinvestor(activityid, termno, investorid, joindate, joinstatus)
                                                SELECT %s, %s, t.investorid, DATE_FORMAT(NOW(), '%Y%m%d'), '0'
                                                FROM siminfo.t_investor t
                                                WHERE t.investoraccounttype = '0' and t.investorstatus = '1'
                                                    AND (t.investorid > (SELECT MAX(investorid) FROM siminfo.t_activityinvestor t1 WHERE t1.activityid = %s)
                                                        OR t.investorid < (SELECT MIN(investorid) FROM siminfo.t_activityinvestor t2 WHERE t2.activityid = %s)
                                                        OR (SELECT count(investorid) FROM siminfo.t_activityinvestor t2 WHERE t2.activityid = %s AND t.investorid = t2.investorid) = 0)"""
                cursor.execute(sql, (activity_id, term_no, activity_id, activity_id, activity_id))

            if join_mode == '2':
                # 赛事新参与投资者数据重置
                logger.info("[reset new activity investor data]......")
                sql = """UPDATE siminfo.t_investorfund t1, siminfo.t_activityinvestor t2
                                        SET
                                          t1.PreBalance = 0,
                                          t1.CurrMargin = 0,
                                          t1.CloseProfit = 0,
                                          t1.Premium = 0,
                                          t1.Deposit = 0,
                                          t1.Withdraw = 0,
                                          t1.Balance = t1.InitialAsset,
                                          t1.Available = t1.InitialAsset,
                                          t1.PreMargin = 0,
                                          t1.FuturesMargin = 0,
                                          t1.OptionsMargin = 0,
                                          t1.PositionProfit = 0,
                                          t1.Profit = 0,
                                          t1.Interest = 0,
                                          t1.Fee = 0,
                                          t1.TotalCollateral = 0,
                                          t1.CollateralForMargin = 0,
                                          t1.PreAccmulateInterest = 0,
                                          t1.AccumulateInterest = 0,
                                          t1.AccumulateFee = 0,
                                          t1.ForzenDeposit = 0,
                                          t1.AccountStatus = 0,
                                          t1.PreMonthAsset = t1.InitialAsset,
                                          t1.PreWeekAsset = t1.InitialAsset,
                                          t1.PreAsset = t1.InitialAsset,
                                          t1.CurrentAsset = t1.InitialAsset,
                                          t1.PreStockValue = 0,
                                          t1.StockValue = 0
                                          WHERE t1.brokersystemid IN (SELECT DISTINCT
                                                                                          t2.brokersystemid 
                                                                                        FROM
                                                                                          siminfo.t_activitysettlementgroup t1,
                                                                                          siminfo.t_brokersystemsettlementgroup t2 
                                                                                        WHERE t1.settlementgroupid = t2.settlementgroupid 
                                                                                          AND t1.activityid = %s)
                                              AND t1.investorid = t2.investorid
                                              AND t2.activityid = %s
                                              AND t2.joinstatus = '0'"""
                cursor.execute(sql, (initial_balance, initial_balance, activity_id, activity_id))
                sql = """DELETE FROM siminfo.t_clientposition 
                                    WHERE clientid IN (SELECT clientid FROM siminfo.t_investorclient t1, siminfo.t_activityinvestor t2, siminfo.t_activitysettlementgroup t3 
                                                    WHERE t1.investorid = t2.investorid AND t2.joinstatus = '0' AND t1.settlementgroupid = t3.settlementgroupid 
                                                    AND t2.activityid = t3.activityid AND t2.activityid = %s)"""
                cursor.execute(sql, (activity_id,))
                sql = """DELETE FROM siminfo.t_clientpositionforsecurityprofit 
                                    WHERE clientid IN (SELECT clientid FROM siminfo.t_investorclient t1, siminfo.t_activityinvestor t2, siminfo.t_activitysettlementgroup t3 
                                                    WHERE t1.investorid = t2.investorid AND t2.joinstatus = '0' AND t1.settlementgroupid = t3.settlementgroupid 
                                                    AND t2.activityid = t3.activityid AND t2.activityid = %s)"""
                cursor.execute(sql, (activity_id,))

            # 赛事新参与投资者评估信息
            sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,TermNo, InvestorID,InitialAsset,PreMonthAsset, PreWeekAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOfMonth,ReturnRateOfWeek,ReturnRateOf1Day)
                                SELECT t2.activityid, %s, t1.investorid, SUM(t1.preasset) AS initialasset, SUM(t1.premonthasset) AS premonthasset, SUM(t1.preweekasset) AS preweekasset, SUM(t1.preasset) AS preasset, SUM(t1.currentasset) AS currasset, 0, 0, 0, 0  FROM siminfo.t_investorfund t1,
                                    (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3, siminfo.t_activity t4
                                    WHERE t1.activityid = %s AND t3.joinstatus = '0' AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid AND t1.activityid = t4.activityid AND t4.activitystatus = '1') t2
                                    WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                    GROUP BY t2.activityid, t1.investorid"""
            cursor.execute(sql, (term_no, activity_id,))

            # 更新投资者参赛状态
            sql = """UPDATE siminfo.t_activityinvestor SET joinstatus = '1' WHERE activityid = %s AND joinstatus = '0'"""
            cursor.execute(sql, (activity_id,))

            # 更新投资者赛事活动评估信息
            logger.info("[calculate investor activity evaluation]......")
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.preasset = t1.currentasset,
                                                  t1.preranking = t1.ranking, t1.ranking = 0, t1.rankingstatus = '0'
                                            WHERE t1.activityid = %s and t1.termno = %s"""
            cursor.execute(sql, (activity_id, term_no))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                            SELECT t2.activityid, t1.investorid, SUM(t1.premonthasset) AS premonthasset, SUM(t1.preweekasset) AS preweekasset, SUM(t1.preasset) AS preasset, SUM(t1.currentasset) AS currasset FROM siminfo.t_investorfund t1,
                                            (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3
                                            WHERE t1.activityid = %s AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid) t2
                                            WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                            GROUP BY t2.activityid, t1.investorid) t2
                                            SET t1.currentasset = t2.currasset, t1.premonthasset = t2.premonthasset, t1.preweekasset = t2.preweekasset, t1.preasset = t2.preasset
                                            WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid AND t1.termno = %s"""
            cursor.execute(sql, (activity_id, term_no))
            # 计算月盈利率、周盈利率
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.totalreturnrate = IF(t1.initialasset =0 , 0, round((t1.currentasset - t1.initialasset) / t1.initialasset, 4)), 
                                                  t1.returnrateof1day = IF(t1.preasset = 0, 0, round((t1.currentasset - t1.preasset) / t1.preasset, 4)),                               
                                                  t1.returnrateofmonth = IF(t1.premonthasset = 0, 0, round((t1.currentasset - t1.premonthasset) / t1.premonthasset, 4)),
                                                  t1.returnrateofweek = IF(t1.preweekasset = 0, 0, round((t1.currentasset - t1.preweekasset) / t1.preweekasset, 4))
                                            WHERE t1.activityid = %s AND t1.termno = %s"""
            cursor.execute(sql, (activity_id, term_no))

            if ranking_rule == "00":
                # 排序规则为00时，全部参与排序
                sql = """UPDATE siminfo.t_activityinvestorevaluation t
                                           SET t.rankingstatus = 1
                                           WHERE t.activityid = %s and t.termno = %s"""
                cursor.execute(sql, (activity_id, term_no,))
            elif ranking_rule == "01":
                # 排序规则为01时，根据投资者设置确定是否参与排名
                sql = """UPDATE siminfo.t_activityinvestorevaluation t, siminfo.t_activityinvestor t1
                                           SET t.rankingstatus = '1'
                                           WHERE t.activityid = %s AND t.termno = %s AND t.activityid = t1.activityid AND t.investorid = t1.investorid AND t1.rankable = '1'"""
                cursor.execute(sql, (activity_id, term_no,))
            elif ranking_rule == "02":
                # 排序规则为02时，不排名
                sql = """UPDATE siminfo.t_activityinvestorevaluation t
                                                           SET t.rankingstatus = '0'
                                                           WHERE t.activityid = %s AND t.termno = %s"""
                cursor.execute(sql, (activity_id, term_no,))
            else:
                # 根据是否真实开户设置rankingstatus，真实开户置为1，否则置为0
                sql = """UPDATE siminfo.t_activityinvestorevaluation t, (SELECT activityid, investorid FROM siminfo.t_activityrankableinvestor WHERE activityid = %s) t1
                                            SET t.rankingstatus = 1
                                            WHERE t.activityid = %s AND t.termno = %s AND t.activityid = t1.activityid AND t.investorid = t1.investorid"""
                cursor.execute(sql, (activity_id,activity_id, term_no,))

            # 废弃用户不参与排名
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1, (SELECT investorid FROM siminfo.t_investor WHERE openid LIKE '%_o') t2
                                        SET t1.rankingstatus = '0' WHERE t1.activityid = %s AND t1.termno = %s AND t1.investorid = t2.investorid"""
            cursor.execute(sql, (activity_id, term_no,))

            # 根据是否参与交易设置rankingstatus，昨资产或今资产不为初始资产置为1，否则置为0
            sql = """UPDATE siminfo.t_activityinvestorevaluation t
                                        SET t.rankingstatus = 0
                                        WHERE t.activityid = %s AND t.termno = %s AND t.preasset = t.initialasset AND t.currentasset = t.initialasset"""
            cursor.execute(sql, (activity_id, term_no,))

            # 设置总收益率排名
            sql = """UPDATE siminfo.t_activityinvestorevaluation t, 
                                    (SELECT t.activityid, t.termno, t.investorid, t.newranking FROM (SELECT t.activityid, t.termno, t.investorid, (@i:=@i+1) AS newranking FROM siminfo.t_activityinvestorevaluation t,(SELECT @i:=0) AS it 
                                        WHERE t.activityid = %s AND t.termno = %s AND t.rankingstatus = '1' 
                                        ORDER BY t.totalreturnrate DESC, t.currentasset DESC, t.returnrateof1day DESC, t.investorid) t) t1
                                    SET t.ranking = t1.newranking 
                                    WHERE t.activityid = t1.activityid AND t.termno = t1.termno AND t.investorid = t1.investorid"""
            cursor.execute(sql, (activity_id, term_no,))

            # 设置参与人数
            logger.info("[update activity joincount]......")
            sql = """UPDATE siminfo.t_activity t, 
                                    (SELECT COUNT(1) as joincount FROM siminfo.t_activityinvestor t3 WHERE t3.activityid = %s) t1
                                    SET t.joincount = t1.joincount 
                                    WHERE t.activityid = %s AND t.termno = %s"""
            cursor.execute(sql, (activity_id, activity_id, term_no,))

            # 更新赛事持仓、资金数据
            logger.info("[update activity investor fund and position]......")
            sql = """DELETE FROM siminfo.t_activityinvestorfund WHERE activityid = %s AND termno = %s"""
            cursor.execute(sql, (activity_id, term_no,))
            sql = """INSERT INTO siminfo.t_activityinvestorfund(TradingDay,ActivityID,TermNo,BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,
                                                                                            AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue)
                                    SELECT distinct %s,%s,%s,t1.BrokerSystemID,t1.InvestorID,t1.PreBalance,t1.CurrMargin,t1.CloseProfit,t1.Premium,t1.Deposit,t1.Withdraw,t1.Balance,t1.Available,t1.PreMargin,t1.FuturesMargin,t1.OptionsMargin,t1.PositionProfit,t1.Profit,t1.Interest,t1.Fee,t1.TotalCollateral,t1.CollateralForMargin,t1.PreAccmulateInterest,t1.AccumulateInterest,t1.AccumulateFee,t1.ForzenDeposit,t1.AccountStatus,
                                                      t1.InitialAsset,t1.PreMonthAsset,t1.PreWeekAsset,t1.PreAsset,t1.CurrentAsset,t1.PreStockValue,t1.StockValue
                                    FROM siminfo.t_investorfund t1, (SELECT DISTINCT
                                                                                                t2.brokersystemid 
                                                                                                FROM
                                                                                                siminfo.t_activitysettlementgroup t1,
                                                                                                siminfo.t_brokersystemsettlementgroup t2 
                                                                                                WHERE t1.settlementgroupid = t2.settlementgroupid 
                                                                                                AND t1.activityid = %s) t2, siminfo.t_activityinvestor t3
                                    WHERE t1.brokersystemid = t2.brokersystemid AND t1.investorid = t3.investorid AND t3.activityid = %s"""
            cursor.execute(sql, (last_trading_day, activity_id, term_no, activity_id, activity_id,))
            sql = """DELETE FROM siminfo.t_activityinvestorposition WHERE activityid = %s and termno = %s"""
            cursor.execute(sql, (activity_id, term_no,))
            sql = """INSERT INTO siminfo.t_activityinvestorposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,
                                                                                                                FrozenPremium,InstrumentID,ParticipantID,ClientID,InvestorID,ActivityID,TermNo)
                                    SELECT distinct %s,t1.SettlementGroupID,t1.SettlementID,t1.HedgeFlag,t1.PosiDirection,t1.YdPosition,t1.Position,t1.LongFrozen,t1.ShortFrozen,t1.YdLongFrozen,t1.YdShortFrozen,t1.BuyTradeVolume,t1.SellTradeVolume,t1.PositionCost,t1.YdPositionCost,t1.UseMargin,t1.FrozenMargin,t1.LongFrozenMargin,t1.ShortFrozenMargin,
                                                      t1.FrozenPremium,t1.InstrumentID,t1.ParticipantID,t1.ClientID,t3.InvestorID,%s,%s
                                    FROM siminfo.t_clientposition t1, (SELECT DISTINCT
                                                                                                t1.settlementgroupid 
                                                                                                FROM
                                                                                                siminfo.t_activitysettlementgroup t1
                                                                                                WHERE t1.activityid = %s) t2, siminfo.t_investorclient t3, siminfo.t_activityinvestor t4
                                    WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.clientid = t3.clientid AND t1.settlementgroupid = t3.settlementgroupid
                                        AND t3.investorid = t4.investorid AND t4.activityid = %s AND t1.tradingday = %s"""
            cursor.execute(sql, (last_trading_day, activity_id, term_no, activity_id, activity_id, current_trading_day,))

            # 更新赛事前N平均收益率和基准收益率
            sql = """INSERT INTO siminfo.t_tradematchdailyavgreturndata(TradingDay, StatisticRankNo, ActivityID, TermNo, MatchTotalProfit, BenchmarkTotalProfit)
                                  SELECT 
                                              %s AS tradingday,
                                              %s AS statisticrankno,
                                              t1.activityid,
                                              t1.termno,
                                              t1.MatchTotalProfit,
                                              ROUND(
                                                (
                                                  t3.closingprice - t2.initialclosingprice
                                                ) / t2.initialclosingprice,
                                                4
                                              ) AS BenchmarkTotalProfit 
                                            FROM
                                              (SELECT 
                                                ActivityID,
                                                TermNo,
                                                ROUND(AVG(TotalReturnRate), 4) AS MatchTotalProfit 
                                              FROM
                                                (SELECT 
                                                  a.activityid,
                                                  a.termno,
                                                  a.investorid,
                                                  (@i := @i + 1) AS newranking,
                                                  a.totalreturnrate 
                                                FROM
                                                  siminfo.t_activityinvestorevaluation a,
                                                  (SELECT 
                                                    @i := 0) AS it 
                                                WHERE a.ActivityID = %s
                                                  -- AND a.RankingStatus = '1' 
                                                  AND a.termNo = %s 
                                                ORDER BY ActivityID,
                                                  TermNo,
                                                  a.totalreturnrate DESC,
                                                  a.currentasset DESC,
                                                  a.returnrateof1day DESC,
                                                  a.investorid) b 
                                              WHERE newranking <= %s
                                              GROUP BY ActivityID,
                                                TermNo) t1,
                                              (SELECT 
                                                t.lastclosingprice AS initialclosingprice 
                                              FROM
                                                siminfo.t_benchmarkmarket t 
                                              WHERE t.stockid = %s AND t.tradingday = 
                                                (SELECT 
                                                  MIN(t1.day) 
                                                FROM
                                                  siminfo.t_tradingcalendar t1 
                                                WHERE t1.day >= 
                                                  (SELECT 
                                                    t.begindate 
                                                  FROM
                                                    siminfo.t_activity t 
                                                  WHERE t.activityid = %s
                                                    AND t.termno = %s) 
                                                  AND t1.tra = 1)) t2,
                                              siminfo.t_benchmarkmarket t3 
                                            WHERE t3.stockid = %s AND t3.tradingday = %s"""
            #cursor.execute(sql, (last_trading_day, statistic_rank_no, activity_id, term_no, statistic_rank_no, bench_stock_id, activity_id, term_no, bench_stock_id, last_trading_day, ))

            # 赛事结束状态设置
            sql = """UPDATE siminfo.t_activity 
                                    SET
                                      activitystatus = 
                                      CASE
                                        WHEN enddate < %s
                                        THEN '2' 
                                        ELSE activitystatus 
                                      END 
                                    WHERE activityid = %s AND termno = %s AND activitystatus = '1'"""
            cursor.execute(sql, (current_trading_day, activity_id, term_no,))

            # 循环赛生成新一期赛事
            if activity_type == "2":
                sql = """SELECT activitystatus,initialbalance,joinmode,rankingrule,activitytype,circlefreq,duration FROM siminfo.t_activity WHERE activityid = %s AND termno = %s"""
                cursor.execute(sql, (activity_id, term_no))
                row = cursor.fetchone()

                if "2" == str(row[0]):
                    circle_freq = str(row[5])
                    duration = int(row[6])
                    begin_date = current_trading_day[0:6] + "01"
                    end_date = None
                    if circle_freq == "1":
                        sql = """SELECT MAX(t.day) FROM siminfo.t_tradingcalendar t WHERE t.day LIKE CONCAT(SUBSTR(DATE_FORMAT(DATE_ADD(%s, INTERVAL %s QUARTER), '%Y%m%d'), 1, 6), '%') """
                        cursor.execute(sql, (last_trading_day, duration))
                        row = cursor.fetchone()
                        end_date = str(row[0])
                    elif circle_freq == "2":
                        sql = """SELECT MAX(t.day) FROM siminfo.t_tradingcalendar t WHERE t.day LIKE CONCAT(SUBSTR(DATE_FORMAT(DATE_ADD(%s, INTERVAL %s MONTH), '%Y%m%d'), 1, 6), '%') """
                        cursor.execute(sql, (last_trading_day, duration))
                        row = cursor.fetchone()
                        end_date = str(row[0])

                    if end_date is not None:
                        logger.info("[gen term %s of circle activity %s]......" % (term_no + 1, activity_id,))
                        sql = """INSERT INTO siminfo.t_activity(activityid, termno, activityname, activitytype, activitystatus, initialbalance, joinmode, rankingrule, CircleFreq, Duration, JoinCount, createdate, createtime, begindate, enddate, updatedate, updatetime)
                                                            SELECT %s, t.termno+1, activityname, activitytype, '1', initialbalance, joinmode, rankingrule, CircleFreq, Duration, JoinCount, DATE_FORMAT(NOW(), '%Y%m%d'), DATE_FORMAT(NOW(), '%H:%i:%S'), %s, %s, DATE_FORMAT(NOW(), '%Y%m%d'), DATE_FORMAT(NOW(), '%H:%i:%S')
                                                            FROM siminfo.t_activity t
                                                            WHERE t.activityid = %s AND t.termno = %s"""
                        cursor.execute(sql, (activity_id, begin_date, end_date, activity_id, term_no))
                        sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,TermNo, InvestorID,InitialAsset,PreMonthAsset, PreWeekAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOfMonth,ReturnRateOfWeek,ReturnRateOf1Day)
                                                        SELECT %s, termno+1,InvestorID,CurrentAsset,PreMonthAsset, PreWeekAsset,PreAsset,CurrentAsset,0,0,0,0
                                                        FROM siminfo.t_activityinvestorevaluation
                                                        WHERE activityid = %s AND termno = %s"""
                        cursor.execute(sql, (activity_id, activity_id, term_no,))
                        # 插入资金、持仓数据
                        sql = """INSERT INTO siminfo.t_activityinvestorfund(TradingDay,ActivityID,TermNo,BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,
                                                                                                        AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue)
                                                SELECT %s,%s,%s,t1.BrokerSystemID,t1.InvestorID,t1.PreBalance,t1.CurrMargin,t1.CloseProfit,t1.Premium,t1.Deposit,t1.Withdraw,t1.Balance,t1.Available,t1.PreMargin,t1.FuturesMargin,t1.OptionsMargin,t1.PositionProfit,t1.Profit,t1.Interest,t1.Fee,t1.TotalCollateral,t1.CollateralForMargin,t1.PreAccmulateInterest,t1.AccumulateInterest,t1.AccumulateFee,t1.ForzenDeposit,t1.AccountStatus,
                                                                  t1.InitialAsset,t1.PreMonthAsset,t1.PreWeekAsset,t1.PreAsset,t1.CurrentAsset,t1.PreStockValue,t1.StockValue
                                                FROM siminfo.t_investorfund t1, (SELECT DISTINCT
                                                                                                            t2.brokersystemid 
                                                                                                            FROM
                                                                                                            siminfo.t_activitysettlementgroup t1,
                                                                                                            siminfo.t_brokersystemsettlementgroup t2 
                                                                                                            WHERE t1.settlementgroupid = t2.settlementgroupid 
                                                                                                            AND t1.activityid = %s) t2, siminfo.t_activityinvestor t3
                                    WHERE t1.brokersystemid = t2.brokersystemid AND t1.investorid = t3.investorid AND t3.activityid = %s"""
                        cursor.execute(sql, (last_trading_day, activity_id, term_no + 1, activity_id, activity_id,))
                        sql = """INSERT INTO siminfo.t_activityinvestorposition(TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,
                                                                                                                            FrozenPremium,InstrumentID,ParticipantID,ClientID,InvestorID,ActivityID,TermNo)
                                                SELECT %s,t1.SettlementGroupID,t1.SettlementID,t1.HedgeFlag,t1.PosiDirection,t1.YdPosition,t1.Position,t1.LongFrozen,t1.ShortFrozen,t1.YdLongFrozen,t1.YdShortFrozen,t1.BuyTradeVolume,t1.SellTradeVolume,t1.PositionCost,t1.YdPositionCost,t1.UseMargin,t1.FrozenMargin,t1.LongFrozenMargin,t1.ShortFrozenMargin,
                                                                  t1.FrozenPremium,t1.InstrumentID,t1.ParticipantID,t1.ClientID,t3.InvestorID,%s,%s
                                                FROM siminfo.t_clientposition t1, (SELECT DISTINCT
                                                                                                            t1.settlementgroupid 
                                                                                                            FROM
                                                                                                            siminfo.t_activitysettlementgroup t1
                                                                                                            WHERE t1.activityid = %s) t2, siminfo.t_investorclient t3, siminfo.t_activityinvestor t4
                                    WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.clientid = t3.clientid AND t1.settlementgroupid = t3.settlementgroupid
                                        AND t3.investorid = t4.investorid AND t4.activityid = %s AND t1.tradingday = %s"""
                        cursor.execute(sql, (last_trading_day, activity_id, term_no + 1, activity_id, activity_id, current_trading_day,))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle activity] Error: %s" % (e))
        result_code = -1
    finally:
        mysql_conn.close()
        logger.info("[settle activity] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files, add_ons=add_ons)

    process_assert(settle_activity(context, conf))


if __name__ == "__main__":
    main()
