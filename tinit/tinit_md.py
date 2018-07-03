# -*- coding: UTF-8 -*-

import os
import json

from utils import log, Configuration, parse_conf_args, process_assert, path, mysql, rsync


def tinit_md(context, conf):
    result_code = 0
    logger = log.get_logger(category="tinitMD")

    # 初始化数据库连接
    mysqlDB = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    # 查询当前交易日
    sql = """SELECT t1.tradingday FROM siminfo.t_tradesystemtradingday t1 WHERE t1.tradesystemid = %s"""
    res = mysqlDB.select(sql, (conf.get("tradesystemid"),))
    current_trading_day = str(res[0][0])

    # 拷贝目标地址
    data_target_dir = conf.get("baseDataHome")

    real_dir_path = path.convert(data_target_dir)
    if not os.path.exists(real_dir_path):
        os.makedirs(str(real_dir_path))

    syncs = conf.get("SyncsFrom")
    for sources in syncs:
        for index, file in enumerate(sources['items']):
            file = file.replace("%y", current_trading_day[0:4]) \
                .replace("%m", current_trading_day[4:6]) \
                .replace("%d", current_trading_day[6:8])
            sources['items'][index] = file

    rsync_config = {"type": "get", "target": data_target_dir, "Syncs": syncs}
    logger.info("[sync all csvs with %s] begin" % json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False))
    try:
        rsync.rsync_groups(context, rsync_config)
    except Exception as e:
        logger.info("[sync all csvs with %s] Error: %s" % (
            json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False), e))
        result_code = -1

    logger.info("[sync all csvs with %s] end" % json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False))

    rsync.rsync_groups(context, conf)

    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["hosts", "mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(tinit_md(context, conf))


if __name__ == "__main__":
    main()
