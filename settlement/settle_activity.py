# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args


def settle_activity(context, conf):
    logger = log.get_logger(category="SettleActivity")

    logger.info("[settle activity %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        for activity_id in conf.get("activities"):
            # 更新投资者赛事活动评估信息
            logger.info("[calculate investor activity evaluation]......")
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.preasset = t1.currentasset
                                            WHERE t1.activityid = %s"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                            SELECT t2.activityid, t1.investorid, SUM(t1.balance) AS currasset  FROM siminfo.t_investorfund t1,
                                            (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3
                                            WHERE t1.activityid = %s AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid) t2
                                            WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                            GROUP BY t2.activityid, t1.investorid) t2
                                            SET t1.currentasset = t2.currasset
                                            WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                            SELECT t1.activityid, t2.investorid, SUM(t4.stockvalue) AS stockvalue FROM siminfo.t_activitysettlementgroup t1, siminfo.t_activityinvestor t2, siminfo.t_investorclient t3, siminfo.t_clientfund t4, 
                                                siminfo.t_tradesystemsettlementgroup t5, siminfo.t_tradesystemtradingday t6
                                            WHERE t1.activityid = %s AND t4.tradingday = t6.tradingday AND t1.activityid = t2.activityid AND t2.investorid = t3.investorid
                                                AND t1.settlementgroupid = t3.settlementgroupid AND t3.clientid = t4.clientid AND t1.settlementgroupid = t5.settlementgroupid AND t5.tradesystemid = t6.tradesystemid
                                                GROUP BY t1.activityid, t2.investorid) t2
                                            SET t1.currentasset = t1.currentasset + t2.stockvalue
                                            WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid"""
            cursor.execute(sql, (activity_id,))
            sql = """UPDATE siminfo.t_activityinvestorevaluation t1
                                            SET t1.totalreturnrate = IF(t1.initialasset =0 , 0, round((t1.currentasset - t1.initialasset) / t1.initialasset, 4)), 
                                                  t1.returnrateof1day = IF(t1.preasset = 0, 0, round((t1.currentasset - t1.preasset) / t1.preasset, 4))
                                            WHERE t1.activityid = %s"""
            cursor.execute(sql, (activity_id,))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle activity] Error: %s" % (e))
    finally:
        mysql_conn.close()
    logger.info("[settle activity] end")


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    settle_activity(context, conf)


if __name__ == "__main__":
    main()