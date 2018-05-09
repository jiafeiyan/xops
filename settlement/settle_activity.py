# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_activity(context, conf):
    result_code = 0
    logger = log.get_logger(category="SettleActivity")

    logger.info("[settle activity %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        # 结算正在进行的赛事数据
        sql = """SELECT activityid FROM siminfo.t_activity WHERE activitystatus != '2'"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        activities = []
        for row in rows:
            activities.append(str(row[0]))

        for activity_id in activities:
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

            sql = """SELECT activitystatus FROM siminfo.t_activity WHERE activityid = %s"""
            cursor.execute(sql, (activity_id,))
            row = cursor.fetchone()

            if "0" == str(row[0]):
                sql = """DELETE FROM siminfo.t_activityinvestorevaluation WHERE activityid = %s"""
                cursor.execute(sql, (activity_id,))

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
                                    WHERE activityid = %s AND activitystatus = '0'"""
            cursor.execute(sql, (current_trading_day, current_trading_day, activity_id))

            sql = """SELECT activitystatus,initialbalance,joinmode,rankingrule,activitytype FROM siminfo.t_activity WHERE activityid = %s"""
            cursor.execute(sql, (activity_id,))
            row = cursor.fetchone()

            if "0" == str(row[0]):
                continue

            initial_balance = str(row[1])
            join_mode = str(row[2])
            ranking_rule = str(row[3])
            activity_type = str(row[4])

            if activity_type == '0':
                # 默认赛事投资者数据
                logger.info("[insert default activity investor]......")
                sql = """INSERT INTO siminfo.t_activityinvestor(activityid, investorid, joindate, joinstatus)
                                                SELECT %s, t.investorid, DATE_FORMAT(NOW(), '%Y%m%d'), '0'
                                                FROM siminfo.t_investor t
                                                WHERE t.investoraccounttype = '0' and t.investorstatus = '1'
                                                    AND (t.investorid > (SELECT MAX(investorid) FROM siminfo.t_activityinvestor t1 WHERE t1.activityid = %s)
                                                        OR t.investorid < (SELECT MIN(investorid) FROM siminfo.t_activityinvestor t2 WHERE t2.activityid = %s)
                                                        OR (SELECT count(investorid) FROM siminfo.t_activityinvestor t2 WHERE t2.activityid = %s) = 0)"""
                cursor.execute(sql, (activity_id, activity_id, activity_id, activity_id))

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
            sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,InvestorID,InitialAsset,PreMonthAsset, PreWeekAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOfMonth,ReturnRateOfWeek,ReturnRateOf1Day)
                                SELECT t2.activityid, t1.investorid, SUM(t1.initialasset) AS initialasset, SUM(t1.premonthasset) AS premonthasset, SUM(t1.preweekasset) AS preweekasset, SUM(t1.preasset) AS preasset, SUM(t1.currentasset) AS currasset, 0, 0, 0, 0  FROM siminfo.t_investorfund t1,
                                    (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3, siminfo.t_activity t4
                                    WHERE t1.activityid = %s AND t3.joinstatus = '0' AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid AND t1.activityid = t4.activityid AND t4.activitystatus = '1') t2
                                    WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                    GROUP BY t2.activityid, t1.investorid"""
            cursor.execute(sql, (activity_id,))

            # 更新投资者参赛状态
            sql = """UPDATE siminfo.t_activityinvestor SET joinstatus = '1' WHERE activityid = %s AND joinstatus = '0'"""
            cursor.execute(sql, (activity_id,))

            # 更新投资者赛事活动评估信息
            logger.info("[calculate investor activity evaluation]......")
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.preasset = t1.currentasset,
                                                  t1.preranking = t1.ranking, t1.ranking = 0, t1.rankingstatus = '0'
                                            WHERE t1.activityid = %s"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                            SELECT t2.activityid, t1.investorid, SUM(t1.premonthasset) AS premonthasset, SUM(t1.preweekasset) AS preweekasset, SUM(t1.preasset) AS preasset, SUM(t1.currentasset) AS currasset FROM siminfo.t_investorfund t1,
                                            (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3
                                            WHERE t1.activityid = %s AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid) t2
                                            WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                            GROUP BY t2.activityid, t1.investorid) t2
                                            SET t1.currentasset = t2.currasset, t1.premonthasset = t2.premonthasset, t1.preweekasset = t2.preweekasset, t1.preasset = t2.preasset
                                            WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid"""
            cursor.execute(sql, (activity_id,))
            # 月份、周变动时计算月盈利率、周盈利率
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.totalreturnrate = IF(t1.initialasset =0 , 0, round((t1.currentasset - t1.initialasset) / t1.initialasset, 4)), 
                                                  t1.returnrateof1day = IF(t1.preasset = 0, 0, round((t1.currentasset - t1.preasset) / t1.preasset, 4)),                               
                                                  t1.returnrateofmonth = IF(MONTH(%s) - MONTH(%s) = 0, t1.returnrateofmonth, IF(t1.premonthasset = 0, 0, round((t1.currentasset - t1.premonthasset) / t1.premonthasset, 4))),
                                                  t1.returnrateofweek = IF(WEEK(%s, 1) - WEEK(%s, 1) = 0, t1.returnrateofweek, IF(t1.preweekasset = 0, 0, round((t1.currentasset - t1.preweekasset) / t1.preweekasset, 4)))
                                            WHERE t1.activityid = %s"""
            cursor.execute(sql, (current_trading_day, last_trading_day, current_trading_day, last_trading_day, activity_id,))

            if ranking_rule == "00":
                # 排序规则为00时，全部参与排序
                sql = """UPDATE siminfo.t_activityinvestorevaluation t
                                           SET t.rankingstatus = 1
                                           WHERE t.activityid = %s"""
                cursor.execute(sql, (activity_id,))
            elif ranking_rule == "01":
                # 排序规则为01时，根据投资者设置确定是否参与排名
                sql = """UPDATE siminfo.t_activityinvestorevaluation t, siminfo.t_activityinvestor t1
                                           SET t.rankingstatus = '1'
                                           WHERE t.activityid = %s AND t.activityid = t1.activityid AND t.investorid = t1.investorid AND t1.rankable = '1'"""
                cursor.execute(sql, (activity_id,))
            else:
                # 根据是否真实开户设置rankingstatus，真实开户置为1，否则置为0
                sql = """UPDATE siminfo.t_activityinvestorevaluation t, (SELECT activityid, investorid FROM siminfo.t_activityrankableinvestor WHERE activityid = %s) t1
                                            SET t.rankingstatus = 1
                                            WHERE t.activityid = %s AND t.activityid = t1.activityid AND t.investorid = t1.investorid"""
                cursor.execute(sql, (activity_id,activity_id,))

                # 根据是否参与交易设置rankingstatus，昨资产或今资产不为初始资产置为1，否则置为0
                sql = """UPDATE siminfo.t_activityinvestorevaluation t
                                            SET t.rankingstatus = 0
                                            WHERE t.activityid = %s AND t.preasset = t.initialasset AND t.currentasset = t.initialasset"""
                cursor.execute(sql, (activity_id,))

            # 设置总收益率排名
            sql = """UPDATE siminfo.t_activityinvestorevaluation t, 
                                    (SELECT t.activityid, t.investorid, t.newranking FROM (SELECT t.activityid, t.investorid, (@i:=@i+1) AS newranking FROM siminfo.t_activityinvestorevaluation t,(SELECT @i:=0) AS it 
                                        WHERE t.activityid = %s AND t.rankingstatus = '1' 
                                        ORDER BY t.totalreturnrate DESC, t.currentasset DESC, t.returnrateof1day DESC, t.investorid) t) t1
                                    SET t.ranking = t1.newranking 
                                    WHERE t.activityid = t1.activityid AND t.investorid = t1.investorid"""
            cursor.execute(sql, (activity_id,))

            # 赛事结束状态设置
            sql = """UPDATE siminfo.t_activity 
                                    SET
                                      activitystatus = 
                                      CASE
                                        WHEN enddate < %s
                                        THEN '2' 
                                        ELSE activitystatus 
                                      END 
                                    WHERE activitystatus = '1'"""
            cursor.execute(sql, (current_trading_day,))

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

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_activity(context, conf))


if __name__ == "__main__":
    main()
