# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def publish_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="PublishFutureBroker")

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')

    broker_system_id = conf.get("brokerSystemId")

    logger.info("[publish future broker %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")

        mysql_conn.commit()
    except Exception as e:
        logger.error("[publish future broker] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[publish future broker] end")
    return result_code


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(publish_future(context, conf))


if __name__ == "__main__":
    main()
