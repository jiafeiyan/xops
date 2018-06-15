# -*- coding: UTF-8 -*-

import os
import json

import rsync
from utils import log, mysql, Configuration, parse_conf_args, process_assert


def snap_data(context, conf):
    result_code = 0
    logger = log.get_logger(category="SnapData")

    broker_system_id = conf.get("brokerSystemId")

    logger.info("[snap data %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[snap t_activityinvestorevaluation]......")
        sql = """INSERT INTO snap.t_s_activityinvestorevaluation ( TradingDay,ActivityID,InvestorID,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOfMonth,ReturnRateOfWeek,ReturnRateOf1Day,RankingStatus,PreRanking,Ranking) SELECT
                    DATE_FORMAT( NOW( ), '%Y%m%d' ),
                    ActivityID,
                    InvestorID,
                    InitialAsset,
                    PreMonthAsset,
                    PreWeekAsset,
                    PreAsset,
                    CurrentAsset,
                    TotalReturnRate,
                    ReturnRateOfMonth,
                    ReturnRateOfWeek,
                    ReturnRateOf1Day,
                    RankingStatus,
                    PreRanking,
                    Ranking
                    FROM
                        siminfo.t_activityinvestorevaluation"""
        cursor.execute(sql)

        mysql_conn.commit()
    except Exception as e:
        logger.error("[snap data] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[snap data] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(snap_data(context, conf))


if __name__ == "__main__":
    main()