#-*- coding: UTF-8 -*-

from utils import Configuration, mysql, log, parse_conf_args


def gen_robots(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="GenRobots")

    settlement_group_id = conf.get("settlementGroupId")
    participant_id = conf.get("participantId")
    id_prefix = conf["prefix"]
    id_int = conf["start"]
    count = conf["count"]

    logger.info("[gen %d robots start with %d] begin" % (count, id_int))

    id_list_1 = []
    id_list_2 = []
    for i in range(0, count):
        id_str = "%s%s" % (id_prefix, str(id_int).rjust(5, "0"))
        id_int += 1
        id_list_1.append((settlement_group_id, id_str, id_str,))
        id_list_2.append((settlement_group_id, participant_id, id_str,))

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        sql = '''INSERT INTO siminfo.t_client(settlementgroupid, clientid, clientname, identifiedcardtype, identifiedcardno, tradingrole, clienttype, isactive, hedgeflag)
                            VALUES (%s, %s, %s, '', '', '1', '0', '1', '1')'''
        cursor.executemany(sql, id_list_1)

        sql = '''INSERT INTO siminfo.t_partclient(settlementgroupid, participantid, clientid)
                            VALUES (%s, %s, %s)'''
        cursor.executemany(sql, id_list_2)

        mysql_conn.commit()

    except Exception as e:
        logger.error("[gen %d robots start with %d] Error: %s" % (count, id_int, e))
    finally:
        mysql_conn.close()

    logger.info("[gen %d robots start with %d] end" % (count, id_int))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_robots(context, conf)


if __name__ == "__main__":
    main()
