# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def publish_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="PublishfutureExchange")

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')

    trade_system_id = conf.get("tradeSystemId")

    logger.info("[publish future exchange %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT DISTINCT t1.tradingday 
                 FROM siminfo.t_tradesystemtradingday t1
                 WHERE t1.tradesystemid = %s"""
        cursor.execute(sql, (trade_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % current_trading_day)

        logger.info("[get next trading day]......")
        sql = """SELECT DAY FROM siminfo.t_TradingCalendar t WHERE t.day > %s AND t.tra = '1' ORDER BY DAY LIMIT 1"""
        cursor.execute(sql, (current_trading_day,))
        row = cursor.fetchone()

        next_trading_day = str(row[0])
        logger.info("[get next trading day] next_trading_day = %s" % next_trading_day)

        # 更新交易所系统交易日
        logger.info("[update trade system tradingday]......")
        sql = """UPDATE siminfo.t_tradesystemtradingday t1 
                SET t1.tradingday = %s 
                WHERE t1.tradingday = %s
                    AND t1.tradesystemid = %s"""
        cursor.execute(sql, (next_trading_day, current_trading_day, trade_system_id))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[publish future exchange] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[publish future exchange] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(publish_future(context, conf))


if __name__ == "__main__":
    main()
