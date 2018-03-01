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

        for activity_id in conf.get("activities"):
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

        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle activity] Error: %s" % (e))
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle activity] end")
    return result_code


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_activity(context, conf))


if __name__ == "__main__":
    main()