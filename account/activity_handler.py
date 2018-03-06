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
                    sql = """SELECT activitystatus FROM siminfo.t_activity WHERE activityid = %s"""
                    cursor.execute(sql, (activity,))
                    row = cursor.fetchone()
                    activity_status = str(row[0])

                    join_status = '0'
                    # 检查投资者资金 持仓
                    if activity_status == '1':
                        sql = """SELECT t1.investorid FROM siminfo.t_investorfund t1
                                                    WHERE t1.brokersystemid = (SELECT DISTINCT t2.brokersystemid 
                                                            FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2 WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = %s)
                                                        AND t1.investorid = %s AND (t1.balance <> 1000000 OR t1.available <> 1000000 OR t1.currmargin <> 0 OR t1.profit <> 0 OR t1.stockvalue <> 0)
                                                    UNION
                                                    SELECT DISTINCT t2.investorid FROM siminfo.t_clientposition t1, siminfo.t_investorclient t2, (SELECT settlementgroupid FROM siminfo.t_activitysettlementgroup WHERE activityid = %s) t3
                                                    WHERE t2.investorid = %s AND t1.clientid = t2.clientid AND t1.settlementgroupid = t2.settlementgroupid AND t2.settlementgroupid = t3.settlementgroupid AND t1.position > 0"""
                        cursor.execute(sql, (activity,investor_id,activity,investor_id,))
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
