#-*- coding: UTF-8 -*-

import os
import json
from utils import Configuration, log, parse_conf_args, mysql


def get_current_tradingday(context, conf):
    logger = log.get_logger(category="GetLastTradingDay")

    logger.info("[get last tradingday with %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False),))

    last_trading_day = ""

    trade_system_id = conf.get("tradeSystemId")
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT t1.tradingday FROM siminfo.t_tradesystemtradingday t1 WHERE t1.tradesystemid = %s"""
        cursor.execute(sql, (trade_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))
        logger.info("[get last trading day]......")
        sql = """select t.day from siminfo.t_tradingcalendar t where t.day < %s and t.tra = 1 order by day desc limit 1"""
        cursor.execute(sql, (current_trading_day,))
        row = cursor.fetchone()

        last_trading_day = str(row[0])
    finally:
        mysql_conn.close()

    logger.info("[get last tradingday with %s] end" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False),))

    return last_trading_day


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    print(get_current_tradingday(context, conf))


if __name__ == "__main__":
    main()
