#-*- coding: UTF-8 -*-

import re

open_id_pattern = re.compile("^\d{11}$")


def join_activity(mysql_conn, parameters):
    open_id = parameters.get("id")
    activity = parameters.get("activity")

    code = "0"
    response = {"id": open_id, "activity": activity}
    result = {"kind": "joinActivity", "code": code, "response": response}

    if open_id is None:
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if activity is None:
        code = "-1"
        error = "请输入赛事代码"
    elif len(activity) != 4:
        code = "-1"
        error = "赛事代码应为4位"

    if mysql_conn is None or not mysql_conn.is_connected():
        code = "-1"
        error = "系统内部错误"

    if code == "-1":
        response.update({"error": error})
        result.update({"code": code, "response": response})

        return result

    mysql_conn.set_charset_collation('utf8')
    mysql_conn.start_transaction()

    cursor = mysql_conn.cursor()

    sql = '''SELECT investorid FROM siminfo.t_investor WHERE openid =  %s'''
    cursor.execute(sql, (open_id,))
    row = cursor.fetchone()

    if row is None:
            code = "-1"
            error = "投资者尚未开户"

            response.update({"error": error})
            result.update({"code": code, "response": response})
    else:
        investor_id = str(row[0])
        sql = '''SELECT activityid FROM siminfo.t_activity WHERE activityid =  %s'''
        cursor.execute(sql, (activity,))
        row = cursor.fetchone()

        if row is None:
                code = "-1"
                error = "赛事活动不存在"

                response.update({"error": error})
                result.update({"code": code, "response": response})
        else:
            sql = '''SELECT activityid, investorid, joindate FROM siminfo.t_activityinvestor WHERE activityid =  %s AND investorid = %s'''
            cursor.execute(sql, (activity, investor_id))
            row = cursor.fetchone()

            if row is None:
                sql = """SELECT t1.activityid, t1.investorid FROM siminfo.t_activityinvestor t1, siminfo.t_activity t2 
                                            WHERE t1.activityid = t2.activityid 
                                                AND t2.activitytype = (SELECT activitytype FROM siminfo.t_activity WHERE (activitystatus = '0' or activitystatus = '1') and activityid = %s)
                                                AND t1.investorid = %s"""
                cursor.execute(sql, (activity, investor_id))
                cursor.fetchall()
                if cursor.rowcount > 0:
                    code = "-1"
                    error = "投资者已参加其他同类型赛事活动"

                    response.update({"error": error})
                    result.update({"code": code, "response": response})
                else:
                    # 获取当前交易日
                    sql = """SELECT DISTINCT t1.tradingday FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2, siminfo.t_activitysettlementgroup t3
                                WHERE t1.tradesystemid = t2.tradesystemid AND t2.settlementgroupid = t3.settlementgroupid AND t3.activityid = %s"""
                    cursor.execute(sql, (activity,))
                    row = cursor.fetchone()
                    current_trading_day = str(row[0])

                    # 检查赛事活动状态
                    sql = """SELECT activitystatus, initialbalance FROM siminfo.t_activity WHERE activityid = %s"""
                    cursor.execute(sql, (activity,))
                    row = cursor.fetchone()
                    activity_status = str(row[0])
                    initial_balance = str(row[1])

                    join_status = '0'
                    # 检查投资者资金 持仓
                    if activity_status == '1':
                        sql = """SELECT t1.investorid FROM siminfo.t_investorfund t1
                                                    WHERE t1.brokersystemid = (SELECT DISTINCT t2.brokersystemid 
                                                            FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2 WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = %s)
                                                        AND t1.investorid = %s AND (t1.balance <> %s OR t1.available <> %s OR t1.currmargin <> 0 OR t1.profit <> 0 OR t1.stockvalue <> 0)
                                                    UNION
                                                    SELECT DISTINCT t2.investorid FROM siminfo.t_clientposition t1, siminfo.t_investorclient t2, (SELECT settlementgroupid FROM siminfo.t_activitysettlementgroup WHERE activityid = %s) t3
                                                    WHERE t2.investorid = %s AND t1.clientid = t2.clientid AND t1.settlementgroupid = t2.settlementgroupid AND t2.settlementgroupid = t3.settlementgroupid AND t1.position > 0"""
                        cursor.execute(sql, (activity,investor_id,initial_balance,initial_balance,activity,investor_id))
                        cursor.fetchall()
                        if cursor.rowcount == 0:
                            sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,InvestorID,InitialAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOf1Day)
                                                SELECT t2.activityid, t1.investorid, SUM(t1.balance) AS initialasset, SUM(t1.balance) AS preasset, SUM(t1.balance) AS currasset, 0, 0  FROM siminfo.t_investorfund t1,
                                                        (SELECT DISTINCT t1.activityid, t2.brokersystemid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2 WHERE t1.activityid = %s AND t1.settlementgroupid = t2.settlementgroupid) t2
                                                        WHERE t1.investorid = %s AND t1.brokersystemid = t2.brokersystemid
                                                        GROUP BY t2.activityid, t1.investorid"""
                            cursor.execute(sql, (activity, investor_id))

                            join_status = '1'

                    sql = """INSERT INTO siminfo.t_activityinvestor(activityid, investorid, joindate, joinstatus) VALUES(%s, %s, DATE_FORMAT(NOW(), '%Y%m%d'), %s)"""
                    cursor.execute(sql, (activity, investor_id, join_status))
                    if cursor.rowcount == 0:
                        code = "-1"
                        error = "参加赛事活动失败"

                        response.update({"error": error})
                        result.update({"code": code, "response": response})

    mysql_conn.commit()

    return result


def query_activity_ranking(mysql_conn, parameters):
    activity_id = parameters.get("activity")
    investor_id = parameters.get("investor")
    query_type = parameters.get("type")
    query_count = parameters.get("count")

    code = "0"
    response = {"activity": activity_id, "investor": investor_id, "type": query_type, "count": query_count}
    result = {"kind": "queryActivityRanking", "code": code, "response": response}

    if activity_id is None:
        code = "-1"
        error = "请输入赛事编号"
    elif len(activity_id) != 4:
        code = "-1"
        error = "赛事代码应为4位"

    if query_type not in ['00', '01', '99']:
        code = "-1"
        error = "查询类型仅支持00、01、99"

    if query_type == '99' and activity_id is None:
        code = "-1"
        error = "请输入投资者代码"

    if query_count is None:
        query_count = 30

    if mysql_conn is None or not mysql_conn.is_connected():
        code = "-1"
        error = "系统内部错误"

    if code == "-1":
        response.update({"error": error})
        result.update({"code": code, "response": response})

        return result

    mysql_conn.set_charset_collation('utf8')

    cursor = mysql_conn.cursor()

    if investor_id is not None and investor_id != "":
        sql = '''SELECT investorid FROM siminfo.t_investor WHERE investorid =  %s'''
        cursor.execute(sql, (investor_id,))
        row = cursor.fetchone()

        if row is None:
            code = "-1"
            error = "投资者尚未开户"

            response.update({"error": error})
            result.update({"code": code, "response": response})

            return result

    rows = None
    if query_type == '99' and investor_id is not None and investor_id != "":
        sql = """SELECT t.investorid, t1.investorname, t.initialasset, t.preasset, t.currentasset, ROUND(t.totalreturnrate, 4), ROUND(t.returnrateof1day, 4), t.rankingstatus, t.preranking, t.ranking
                                FROM siminfo.t_activityinvestorevaluation t, siminfo.t_investor t1
                                WHERE t.activityid = %s AND t.investorid = %s AND t.investorid = t1.investorid"""
        cursor.execute(sql, (activity_id, investor_id,))
        rows = cursor.fetchall()

    if query_type == '00':
        if investor_id is not None and investor_id != "":
            sql = """SELECT t.investorid, t1.investorname, t.initialasset, t.preasset, t.currentasset, ROUND(t.totalreturnrate, 4), ROUND(t.returnrateof1day, 4), t.rankingstatus, t.preranking, t.ranking
                                    FROM siminfo.t_activityinvestorevaluation t, siminfo.t_investor t1
                                    WHERE t.activityid = %s AND ((t.rankingstatus = '1' AND (t.ranking <= %s OR %s = '0')) OR t.investorid = %s) AND t.investorid = t1.investorid
                                    ORDER BY t.rankingstatus DESC, t.ranking"""
            cursor.execute(sql, (activity_id, query_count, query_count, investor_id))
            rows = cursor.fetchall()
        else:
            sql = """SELECT t.investorid, t1.investorname, t.initialasset, t.preasset, t.currentasset, ROUND(t.totalreturnrate, 4), ROUND(t.returnrateof1day, 4), t.rankingstatus, t.preranking, t.ranking
                                    FROM siminfo.t_activityinvestorevaluation t, siminfo.t_investor t1
                                    WHERE t.activityid = %s AND t.rankingstatus = '1' AND (t.ranking <= %s OR %s = '0') AND t.investorid = t1.investorid
                                    ORDER BY t.rankingstatus DESC, t.ranking"""
            cursor.execute(sql, (activity_id, query_count, query_count))
            rows = cursor.fetchall()

    if query_type == '01':
        if investor_id is not None and investor_id != "":
            sql = """SELECT t.investorid, t1.investorname, t.initialasset, t.preasset, t.currentasset, ROUND(t.totalreturnrate, 4), ROUND(t.returnrateof1day, 4), t.rankingstatus, 0 as preranking, t.newranking AS ranking 
                                FROM (SELECT t.* FROM
                                            (SELECT t.*, (@i:=@i+1) AS newranking FROM siminfo.t_activityinvestorevaluation t,(SELECT @i:=0) AS it
                                            WHERE t.activityid = %s AND t.rankingstatus = '1' 
                                            ORDER BY t.returnrateof1day DESC, t.totalreturnrate DESC, t.currentasset DESC, t.investorid) t WHERE t.newranking <= %s OR %s = '0'
                                        UNION ALL
                                        SELECT t.*, 0 AS newranking FROM siminfo.t_activityinvestorevaluation t
                                        WHERE t.activityid = %s AND t.rankingstatus = '0' AND t.investorid = %s
                                        ) t, siminfo.t_investor t1 WHERE t.investorid = t1.investorid"""
            cursor.execute(sql, (activity_id, query_count, query_count, activity_id, investor_id))
            rows = cursor.fetchall()
        else:
            sql = """SELECT t.investorid, t1.investorname, t.initialasset, t.preasset, t.currentasset, ROUND(t.totalreturnrate, 4), ROUND(t.returnrateof1day, 4), t.rankingstatus, 0 as preranking, t.newranking AS ranking 
                                    FROM (SELECT t.*, (@i:=@i+1) AS newranking FROM siminfo.t_activityinvestorevaluation t,(SELECT @i:=0) AS it
                                        WHERE t.activityid = %s AND t.rankingstatus = '1' 
                                        ORDER BY t.returnrateof1day DESC, t.totalreturnrate DESC, t.currentasset DESC, t.investorid) t, siminfo.t_investor t1 WHERE (t.newranking <= %s OR %s = '0') AND t.investorid = t1.investorid"""
            cursor.execute(sql, (activity_id, query_count, query_count))
            rows = cursor.fetchall()

    data = []
    if rows is not None:
        for row in rows:
            data.append({"investorId": str(row[0]),"investorName": str(row[1]),"initialAsset": str(row[2]),"preAsset": str(row[3]),
                                    "currentAsset": str(row[4]),"totalReturnRate": str(row[5]),"returnRateOf1Day": str(row[6]),"rankingStatus": str(int(row[7])),
                                        "preRanking": str(int(row[8])),"ranking": str(int(row[9]))})

    response.update({"data": data})
    result.update({"code": code, "response": response})

    return result


def query_activity_joinstatus(mysql_conn, parameters):
    activity_id = parameters.get("activity")
    open_id = parameters.get("id")

    code = "0"
    response = {"activity": activity_id, "id": open_id, "status" : "-1"}
    result = {"kind": "queryActivityJoinStatus", "code": code, "response": response}

    if open_id is None or open_id == "":
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if activity_id is None or activity_id == "":
        code = "-1"
        error = "请输入赛事代码"
    elif len(activity_id) != 4:
        code = "-1"
        error = "赛事代码应为4位"

    if mysql_conn is None or not mysql_conn.is_connected():
        code = "-1"
        error = "系统内部错误"

    if code == "-1":
        response.update({"error": error})
        result.update({"code": code, "response": response})

        return result

    mysql_conn.set_charset_collation('utf8')

    cursor = mysql_conn.cursor()

    sql = '''SELECT investorid FROM siminfo.t_investor WHERE openid =  %s'''
    cursor.execute(sql, (open_id,))
    row = cursor.fetchone()

    if row is None:
            code = "-1"
            error = "投资者尚未开户"

            response.update({"error": error})
            result.update({"code": code, "response": response})
    else:
        investor_id = str(row[0])
        sql = '''SELECT activityid FROM siminfo.t_activity WHERE activityid =  %s'''
        cursor.execute(sql, (activity_id,))
        row = cursor.fetchone()

        if row is None:
                code = "-1"
                error = "赛事活动不存在"

                response.update({"error": error})
                result.update({"code": code, "response": response})
        else:
            sql = '''SELECT activityid, investorid, joindate FROM siminfo.t_activityinvestor WHERE activityid =  %s AND investorid = %s'''
            cursor.execute(sql, (activity_id, investor_id))
            row = cursor.fetchone()

            if row is not None:
                response.update({"status": "1"})
                result.update({"code": code, "response": response})

    return result
