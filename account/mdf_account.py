#-*- coding: UTF-8 -*-

import sys
import json

from utils import Configuration, mysql, log, parse_conf_args


def mdf_investors(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="MdfAccount")

    logger.info("[mdf investor with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        for account in conf["accounts"]:
            investor_id = account["id"]
            investor_name = account["name"]
            open_id = account["openId"]
            investor_password = account["password"]

            logger.error("[mdf investor with {id=%s, name=%s, openId=%s, password=%s}]......" % (investor_id, investor_name, open_id, investor_password))

            sql = '''SELECT investorid FROM siminfo.t_investor WHERE investorid = %s for update'''
            cursor.execute(sql, (investor_id,))
            row = cursor.fetchone()

            if row is None:
                sys.stderr.write("Error: Investor %s is not existed.\n" % (investor_id,))
                logger.error("[mdf investor with {id=%s, name=%s, openId=%s, password=%s}] Error: Investor %s is not existed." % (investor_id, investor_name, open_id, investor_password, investor_id))
            else:
                sql = '''UPDATE siminfo.t_investor set investorname = %s, openid = %s, password = %s WHERE investorid = %s'''
                cursor.execute(sql, (investor_name, open_id, investor_password, investor_id,))

        mysql_conn.commit()

    except Exception as e:
        logger.error("[mdf investor with %s] Error: %s" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False), e))
    finally:
        mysql_conn.close()

    logger.info("[mdf investor with %s] end" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    mdf_investors(context, conf)


if __name__ == "__main__":
    main()