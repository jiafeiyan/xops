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
                sql = '''INSERT INTO siminfo.t_activityinvestor(activityid, investorid, joindate) VALUES(%s, %s, DATE_FORMAT(NOW(), '%Y%m%d'))'''
                cursor.execute(sql, (activity, investor_id))
                if cursor.rowcount == 0:
                    code = "-1"
                    error = "参加赛事活动失败"

                    response.update({"error": error})
                    result.update({"code": code, "response": response})
                else:
                    sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,InvestorID,InitialAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOf1Day)
                                        SELECT t2.activityid, t1.investorid, SUM(t1.balance) AS initialasset, SUM(t1.balance) AS preasset, SUM(t1.balance) AS currasset, 0, 0  FROM siminfo.t_investorfund t1,
                                            (SELECT DISTINCT t1.activityid, t2.brokersystemid, t3.investorid FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2, siminfo.t_activityinvestor t3
                                            WHERE t1.activityid = %s AND t3.investorid = %s AND t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = t3.activityid) t2
                                            WHERE t1.investorid = t2.investorid AND t1.brokersystemid = t2.brokersystemid
                                            GROUP BY t2.activityid, t1.investorid"""
                    cursor.execute(sql, (activity, investor_id))
                    sql = """UPDATE siminfo.t_activityinvestorevaluation t1,(
                                        SELECT t1.activityid, t2.investorid, SUM(t4.stockvalue) AS stockvalue FROM siminfo.t_activitysettlementgroup t1, siminfo.t_activityinvestor t2, siminfo.t_investorclient t3, siminfo.t_clientfund t4, 
                                            siminfo.t_tradesystemsettlementgroup t5, siminfo.t_tradesystemtradingday t6
                                        WHERE t1.activityid = %s AND t2.investorid = %s AND t4.tradingday = t6.tradingday AND t1.activityid = t2.activityid AND t2.investorid = t3.investorid
                                            AND t1.settlementgroupid = t3.settlementgroupid AND t3.clientid = t4.clientid AND t1.settlementgroupid = t5.settlementgroupid AND t5.tradesystemid = t6.tradesystemid
                                            GROUP BY t1.activityid, t2.investorid) t2
                                        SET t1.initialasset = t1.initialasset + t2.stockvalue, t1.preasset = t1.preasset + t2.stockvalue, t1.currentasset = t1.currentasset + t2.stockvalue
                                        WHERE t1.activityid = t2.activityid AND t1.investorid = t2.investorid"""
                    cursor.execute(sql, (activity, investor_id))

    mysql_conn.commit()

    return result
