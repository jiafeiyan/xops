#-*- coding: UTF-8 -*-

from utils import Configuration, mysql, log, parse_conf_args


def gen_investors(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="GenAccount")

    begin = conf["begin"]
    count = conf["count"]
    end = conf["end"]
    settlement_group_id = conf["SettlementGroupID"]
    client_prefix = conf["ClientPrefix"]

    logger.info("[gen %d investors start with %d count %s end %s] begin" % (count, begin, count, end))

    id_list_all = []
    id_list_1000 = []
    id_int = begin

    gen_count = 0
    for i in range(0, count):
        while True:
            if 0 < end < id_int:
                break
            gen_count += 1
            id_str = str(id_int).rjust(8, "0")
            id_int += 1
            if id_str.find("4") < 0:
                id_list_1000.append((id_str,))
                if len(id_list_1000) == 1000:
                    id_list_all.append(id_list_1000)
                    id_list_1000 = []
                break

    if 0 < len(id_list_1000) < 1000:
        id_list_all.append(id_list_1000)

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        sql = '''INSERT INTO siminfo.t_investorclient(settlementgroupid, investorid, clientid)
                  SELECT %s, InvestorID , CONCAT(%s, investorid) 
                  FROM siminfo.t_investor'''
        cursor.execute(sql, (settlement_group_id, client_prefix))

        sql = '''INSERT INTO siminfo.t_client(settlementgroupid, clientid, clientname, identifiedcardtype, identifiedcardno, tradingrole, clienttype, isactive, hedgeflag)
                            SELECT t2.settlementgroupid, t2.clientid, t2.clientid, '', '', '1', '0', '1', '1'
                            FROM siminfo.t_investor t1, siminfo.t_investorclient t2
                            WHERE t1.investorid = t2.investorid and SettlementGroupID = %s'''
        cursor.execute(sql, (settlement_group_id,))

        sql = '''INSERT INTO siminfo.t_partclient(settlementgroupid, participantid, clientid)
                            SELECT t1.settlementgroupid, t1.participantid, t2.clientid
                            FROM siminfo.t_participant t1, siminfo.t_investorclient t2, siminfo.t_investor t3
                            WHERE t1.settlementgroupid = t2.settlementgroupid AND t2.investorid = t3.investorid AND t1.SettlementGroupID = %s'''
        cursor.execute(sql, (settlement_group_id,))

        mysql_conn.commit()

    except Exception as e:
        logger.error("[gen %d investors start with %d %d count %s end %s] Error: %s" % (count, begin, count, end, e))
    finally:
        mysql_conn.close()

    logger.info("[gen %d investors start with %d count %s end %s, generated %s] end" % (count, begin, count, end, gen_count))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_investors(context, conf)


if __name__ == "__main__":
    main()
