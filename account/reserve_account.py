#-*- coding: UTF-8 -*-
import json
from utils import Configuration, mysql, log, parse_conf_args


def reserve_accounts(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="ReserveAccounts")

    logger.info("[reserve accounts with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        sql = """UPDATE siminfo.t_investor t SET t.investorstatus = '6' WHERE t.investorstatus = '0' AND t.investorid < '00001000'"""
        cursor.execute(sql)

        sql = """UPDATE siminfo.t_investor t SET t.investorstatus = '6' WHERE t.investorstatus = '0' AND t.investorid REGEXP '^0*(1{2,8}|2{2,8}|3{2,8}|5{2,8}|6{2,8}|7{2,8}|8{2,8}|9{2,8})$'"""
        cursor.execute(sql)

        mysql_conn.commit()

    except Exception as e:
        logger.error("[reserve accounts] Error: %s" % (e))
    finally:
        mysql_conn.close()

    logger.info("[reserve accounts with %s] end" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    reserve_accounts(context, conf)


if __name__ == "__main__":
    main()