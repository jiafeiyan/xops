#-*- coding: UTF-8 -*-

import sys
import json

from utils import Configuration, mysql, log, parse_conf_args


def gen_activity(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="GenActivity")

    logger.info("[gen activity with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        for activity in conf["activities"]:
            code = activity["code"]
            name = activity["name"]
            atype = activity["type"]
            begin = activity["begin"]
            end = activity["end"]
            settlement_groups = activity["settlement_groups"]

            logger.info("[gen activity with {code=%s, name=%s, type= %s, begin=%s, end=%s, settlementgroups=%s}]......" % (code, name, atype, begin, end, settlement_groups))

            sql = '''SELECT activityid FROM siminfo.t_activity WHERE activityid = %s'''
            cursor.execute(sql, (code,))
            row = cursor.fetchone()

            if row is not None:
                sys.stderr.write("Error: Activity %s is existed.\n" % (code,))
                logger.error("[gen activity with {code=%s, name=%s, type= %s, begin=%s, end=%s, settlementgroups=%s}] Error: Activity %s is existed." % (code, name, atype, begin, end, settlement_groups, code))
            else:
                sql = '''INSERT INTO siminfo.t_activity(activityid, activityname, activitytype, activitystatus, createdate, createtime, begindate, enddate, updatedate, updatetime)
                                    VALUES (%s, %s, %s, '0', DATE_FORMAT(NOW(), '%Y%m%d'), DATE_FORMAT(NOW(), '%H:%i:%S'), %s, %s, DATE_FORMAT(NOW(), '%Y%m%d'), DATE_FORMAT(NOW(), '%H:%i:%S'))'''
                cursor.execute(sql, (code, name, atype, begin, end,))

                relations = []
                for settlement_group_id in settlement_groups:
                    relations.append((code, settlement_group_id,))

                sql = '''INSERT INTO siminfo.t_activitysettlementgroup(activityid, settlementgroupid) values (%s, %s)'''
                cursor.executemany(sql, relations)

        mysql_conn.commit()

    except Exception as e:
        logger.error("[gen activity with %s] Error: %s" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False), e))
    finally:
        mysql_conn.close()

    logger.info("[gen activity with %s] end" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))


def main():

    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_activity(context, conf)


if __name__ == "__main__":
    main()