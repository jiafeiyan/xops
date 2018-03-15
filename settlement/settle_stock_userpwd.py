# -*- coding: UTF-8 -*-

import json
import csv
from itertools import islice

from utils import Configuration, mysql, log, parse_conf_args, process_assert, path


def settle_stock_userpwd(context, conf):
    result_code = 0
    logger = log.get_logger(category="SettleStockUserPwd")

    logger.info("[settle stock user pwd %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))

    mdf_list_all = []
    mdf_list_1000 = []

    user_file = path.convert(conf.get("dumpUserFile"))

    input_file = csv.reader(open(user_file))
    for line in islice(input_file, 1, None):
        if line[7] == "3":
            mdf_list_1000.append((line[4], line[0],))
        if len(mdf_list_1000) == 1000:
            mdf_list_all.append(mdf_list_1000)
            mdf_list_1000 = []

    if 0 < len(mdf_list_1000) < 1000:
        mdf_list_all.append(mdf_list_1000)

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        for mdf_list in mdf_list_all:
            sql = """UPDATE siminfo.t_investor SET password = %s, investorstatus = '3' WHERE investorid = %s AND investorstatus != '0'"""
            cursor.executemany(sql, mdf_list)

        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle stock user pwd] Error: %s" % (e))
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle stock user pwd] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_stock_userpwd(context, conf))


if __name__ == "__main__":
    main()