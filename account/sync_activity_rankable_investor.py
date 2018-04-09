#-*- coding: UTF-8 -*-

import os
import json

from utils import Configuration, mysql, oracle, log, parse_conf_args


def sync_rankable_activity_investors(context, conf):
    #os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    oracle_pool = oracle(configs=context.get("oracle").get(conf.get("oracleId")))

    logger = log.get_logger(category="SyncRankableActivityInvestors")

    logger.info("[sync activity rankable investors with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    oracle_conn = oracle_pool.get_cnx()

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        oracle_cursor = oracle_conn.cursor()

        mysql_conn.start_transaction()

        mysql_cursor = mysql_conn.cursor()

        for activity_info in conf["activities"]:
            activity_id = activity_info["id"]
            depart_id = activity_info["depart"]
            start_date = activity_info["startDate"]

            sql = '''select distinct :ActivityID as activityid, sj as openid from hxcenter.vkhxx3620 where yyb= :DepartID'''# and khzt='0' and khrq>=:StartDate'''
            #oracle_cursor.execute(sql, {"ActivityID": activity_id, "DepartID": depart_id, "StartDate": start_date})
            oracle_cursor.execute(sql, {"ActivityID": activity_id, "DepartID": depart_id})
            rows = oracle_cursor.fetchall()

            activity_investors = []
            for row in rows:
                activity_investors.append((str(row[0]), str(row[1]).strip()))

            sql = """DELETE FROM siminfo.t_activityrankableinvestor where activityid = %s"""
            mysql_cursor.execute(sql, (activity_id,))

            if len(activity_investors) > 0:
                sql = """INSERT INTO siminfo.t_activityrankableinvestor(activityid, investorid, openid) VALUES (%s, '0', %s)"""
                mysql_cursor.executemany(sql, activity_investors)

                sql = """UPDATE siminfo.t_activityrankableinvestor t, siminfo.t_investor t1 SET t.investorid = t1.investorid WHERE t.activityid = %s AND t.openid = t1.openid"""
                mysql_cursor.execute(sql, (activity_id,))

        mysql_conn.commit()

    except Exception as e:
        logger.error("[sync activity rankable investors with %s] Error: %s" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False), e))
    finally:
        oracle_conn.close()
        mysql_conn.close()

    logger.info("[sync activity rankable investors with %s] end" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "oracle"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    sync_rankable_activity_investors(context, conf)


if __name__ == "__main__":
    main()
