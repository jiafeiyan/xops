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
        sql = """SELECT * FROM siminfo.t_activity WHERE activitystatus = '1'"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        activities = []
        for row in rows:
            activities.append(str(row[0]))

        for activity_id in activities:
            # 获取当前交易日
            logger.info("[get current trading day for activity %s]......" % activity_id)
            sql = """SELECT DISTINCT t1.tradingday FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2, siminfo.t_activitysettlementgroup t3
                        WHERE t1.tradesystemid = t2.tradesystemid AND t2.settlementgroupid = t3.settlementgroupid AND t3.activityid = %s"""
            cursor.execute(sql, (activity_id,))
            row = cursor.fetchone()

            current_trading_day = str(row[0])
            logger.info("[get current trading day for activity %s] current_trading_day = %s" % (activity_id, current_trading_day))

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
                                    WHERE activitystatus = '0'"""
            cursor.execute(sql, (current_trading_day, current_trading_day))
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
                                      t1.Balance = 1000000,
                                      t1.Available = 1000000,
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
            cursor.execute(sql, (activity_id, activity_id,))
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
            sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,InvestorID,InitialAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOf1Day)
                                SELECT t2.activityid, t1.investorid, SUM(t1.balance) AS initialasset, SUM(t1.balance) AS preasset, SUM(t1.balance) AS currasset, 0, 0  FROM siminfo.t_investorfund t1,
                                    (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3, siminfo.t_activity t4
                                    WHERE t1.activityid = %s AND t3.joinstatus = '0' AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid AND t1.activityid = t4.activityid AND t4.activitystatus = '1') t2
                                    WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                    GROUP BY t2.activityid, t1.investorid"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestor SET joinstatus = '1' WHERE activityid = %s AND joinstatus = '0'"""
            cursor.execute(sql, (activity_id,))

            # 更新投资者赛事活动评估信息
            logger.info("[calculate investor activity evaluation]......")
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.preasset = t1.currentasset
                                            WHERE t1.activityid = %s"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                            SELECT t2.activityid, t1.investorid, SUM(t1.balance) AS currasset, SUM(t1.stockvalue) AS stockvalue FROM siminfo.t_investorfund t1,
                                            (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3
                                            WHERE t1.activityid = %s AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid) t2
                                            WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                            GROUP BY t2.activityid, t1.investorid) t2
                                            SET t1.currentasset = t2.currasset + t2.stockvalue
                                            WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.totalreturnrate = IF(t1.initialasset =0 , 0, round((t1.currentasset - t1.initialasset) / t1.initialasset, 4)), 
                                                  t1.returnrateof1day = IF(t1.preasset = 0, 0, round((t1.currentasset - t1.preasset) / t1.preasset, 4))
                                            WHERE t1.activityid = %s"""
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