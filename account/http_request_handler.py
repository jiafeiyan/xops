#-*- coding: UTF-8 -*-

import re

open_id_pattern = re.compile("^\d{11}$")


def open_account(mysql_conn, parameters):
    open_id = parameters.get("id")
    open_name = parameters.get("name")
    activity = parameters.get("activity")

    code = "0"
    response = {"id": open_id, "activity": activity}
    result = {"kind": "openAccount", "code": code, "response": response}

    if open_id is None or open_id == "":
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    set_open_name = True
    if open_name is None or open_name == "":
        open_name = open_id
        set_open_name = False
    elif len(open_name) > 20:
        code = "-1"
        error = "姓名超长"

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

    sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE investorstatus = '0' ORDER BY investorid LIMIT 1 FOR UPDATE'''
    cursor.execute(sql)
    row = cursor.fetchone()

    if activity is None or activity == "":
        if row is None:
            sql = """SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investoraccounttype ='0'"""
            cursor.execute(sql, (open_id,))
            row = cursor.fetchone()

            if row is None:
                code = "-1"
                error = "暂无可用账户"

                response.update({"error": error})
                result.update({"code": code, "response": response})
            else:
                account = str(row[0])
                password = str(row[3])

                response.update({"account": account, "password": password})
                result.update({"response": response})
        else:
            account = str(row[0])
            password = str(row[3])

            sql = """SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investoraccounttype ='0'"""
            cursor.execute(sql, (open_id,))
            row = cursor.fetchone()

            if row is not None:
                account = str(row[0])
                password = str(row[3])

                if set_open_name:
                    sql = '''UPDATE siminfo.t_investor SET investorname = %s WHERE investorid = %s'''
                    cursor.execute(sql,(open_name, account))

                response.update({"account": account, "password": password})
                result.update({"response": response})
            else:
                sql = '''UPDATE siminfo.t_investor SET investorname = IF(investorname is NULL, %s, IF(%s = %s, investorname, %s)), openid = %s, investorstatus = '1' WHERE investorid = %s'''
                cursor.execute(sql,(open_name, open_id, open_name, open_name, open_id, account))

                if cursor.rowcount == 1:
                    response.update({"account": account, "password": password})
                    result.update({"response": response})
                else:
                    code = "-1"
                    error = "开户失败：更新投资者信息失败"

                    response.update({"error": error})
                    result.update({"code": code, "response": response})
    else:
        if row is None:
            sql = '''SELECT joinmode FROM siminfo.t_activity WHERE activityid =  %s AND activitystatus in ('0', '1')'''
            cursor.execute(sql, (activity,))
            row = cursor.fetchone()
            if row is None:
                code = "-1"
                error = "赛事活动不存在或已过期"

                response.update({"error": error})
                result.update({"code": code, "response": response})
            else:
                join_mode = str(row[0])
                if join_mode == "1":
                    code = "-1"
                    error = "暂无可用账户"

                    response.update({"error": error})
                    result.update({"code": code, "response": response})
                else:
                    sql = """SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investoraccounttype ='0'"""
                    cursor.execute(sql, (open_id,))
                    row = cursor.fetchone()

                    if row is None:
                        code = "-1"
                        error = "暂无可用账户"

                        response.update({"error": error})
                        result.update({"code": code, "response": response})
                    else:
                        account = str(row[0])
                        password = str(row[3])

                        response.update({"account": account, "password": password})
                        result.update({"response": response})
        else:
            account = str(row[0])
            password = str(row[3])

            sql = '''SELECT joinmode FROM siminfo.t_activity WHERE activityid =  %s AND activitystatus in ('0', '1')'''
            cursor.execute(sql, (activity,))
            row = cursor.fetchone()
            if row is None:
                code = "-1"
                error = "赛事活动不存在或已过期"

                response.update({"error": error})
                result.update({"code": code, "response": response})
            else:
                join_mode = str(row[0])

                sql = '''SELECT t1.investorid, t1.investorname, t1.openid, t1.PASSWORD, t1.investorstatus
                                                FROM siminfo.t_investor t1, siminfo.t_activityinvestor t2
                                                WHERE t1.openid = %s 
                                                AND t2.activityid = %s AND t1.investorid = t2.investorid'''
                cursor.execute(sql, (open_id, activity))
                row = cursor.fetchone()
                if row is not None:
                    account = str(row[0])
                    password = str(row[3])

                    response.update({"account": account, "password": password})
                    result.update({"response": response})
                else:
                    sql = """SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investoraccounttype ='0'"""
                    cursor.execute(sql, (open_id,))
                    row = cursor.fetchone()

                    if row is not None and join_mode != "1":
                        account = str(row[0])
                        password = str(row[3])

                        response.update({"account": account, "password": password})
                        result.update({"response": response})
                    else:
                        sql = """SELECT investorid
                                        FROM siminfo.t_investor t1
                                        WHERE t1.openid = %s 
                                        AND t1.investorid != %s
                                        AND t1.investoraccounttype = '0'"""
                        cursor.execute(sql,(open_id, account))
                        row = cursor.fetchone()

                        account_type = '1'
                        if row is None:
                            account_type = '0'

                        sql = '''UPDATE siminfo.t_investor t SET t.investorname = %s, t.openid = %s, t.investorstatus = '1', 
                                                  t.investoraccounttype = %s WHERE investorid = %s'''
                        cursor.execute(sql,(open_name, open_id, account_type, account))

                        if cursor.rowcount == 1:
                            response.update({"account": account, "password": password})
                            result.update({"response": response})
                        else:
                            code = "-1"
                            error = "开户失败：更新投资者信息失败"

                            response.update({"error": error})
                            result.update({"code": code, "response": response})

    mysql_conn.commit()

    if code == "0" and activity is not None and activity != "":
        join_result = join_activity_with_account(mysql_conn, {"account": account, "activity": activity})

        if join_result.get("code") != "0":
            code = "-2"
            error = join_result.get("response").get("error")

            response.update({"error": error})
            result.update({"code": code, "response": response})

    return result


def open_activity_account(mysql_conn, parameters):
    open_id = parameters.get("id")
    open_name = parameters.get("name")
    activity = parameters.get("activity")

    code = "0"
    response = {"id": open_id, "activity": activity}
    result = {"kind": "openActivityAccount", "code": code, "response": response}

    if open_id is None or open_id == "":
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if open_name is None or open_name == "":
        code = "-1"
        error = "请输入姓名"
    elif len(open_name) > 20:
        code = "-1"
        error = "姓名超长"

    if activity is None or activity == "":
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

    sql = """SELECT joinmode FROM siminfo.t_activity WHERE activityid = %s"""
    cursor.execute(sql, (activity,))
    row = cursor.fetchone()

    join_mode = str(row[0])

    if join_mode != '1':
        code = "-1"
        error = "赛事活动无需新建账户"

        response.update({"error": error})
        result.update({"code": code, "response": response})

        return result

    sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE investorstatus = '0' ORDER BY investorid LIMIT 1 FOR UPDATE'''
    cursor.execute(sql)
    row = cursor.fetchone()

    if row is None:
        sql = """SELECT t1.investorid, t1.investorname, t1.openid, t1.PASSWORD, t1.investorstatus
                            FROM siminfo.t_investor t1, siminfo.t_activityinvestor t2, siminfo.t_activity t3
                            WHERE t1.openid = %s AND t1.investoraccounttype ='1'
                            AND t2.activityid = %s AND t1.investorid = t2.investorid AND t2.activityid = t3.activityid"""
        cursor.execute(sql, (open_id, activity))
        row = cursor.fetchone()

        if row is None:
            code = "-1"
            error = "暂无可用账户"

            response.update({"error": error})
            result.update({"code": code, "response": response})
        else:
            account = str(row[0])
            password = str(row[3])

            response.update({"account": account, "password": password})
            result.update({"response": response})
    else:
        account = str(row[0])
        password = str(row[3])

        sql = '''SELECT t1.investorid, t1.investorname, t1.openid, t1.PASSWORD, t1.investorstatus
                            FROM siminfo.t_investor t1, siminfo.t_activityinvestor t2, siminfo.t_activity t3
                            WHERE t1.openid = %s AND t1.investoraccounttype ='1'
                            AND t2.activityid = %s AND t1.investorid = t2.investorid AND t2.activityid = t3.activityid'''
        cursor.execute(sql, (open_id, activity))
        row = cursor.fetchone()

        if row is not None:
            account = str(row[0])
            password = str(row[3])

            response.update({"account": account, "password": password})
            result.update({"response": response})
        else:
            sql = '''UPDATE siminfo.t_investor t SET t.investorname = %s, t.openid = %s, t.investorstatus = '1', 
                                      t.investoraccounttype = IF((SELECT joinmode from siminfo.t_activity where activityid = %s) = '1', '1', '0') WHERE investorid = %s'''
            cursor.execute(sql,(open_name, open_id, activity, account))

            if cursor.rowcount == 1:
                response.update({"account": account, "password": password})
                result.update({"response": response})
            else:
                code = "-1"
                error = "开户失败：更新投资者信息失败"

                response.update({"error": error})
                result.update({"code": code, "response": response})

    return result


def open_vip_account(mysql_conn, parameters):
    open_id = parameters.get("id")
    open_name = parameters.get("name")
    activity = parameters.get("activity")
    account = parameters.get("account")

    code = "0"
    response = {"id": open_id, "activity": activity, "account": account}
    result = {"kind": "openVipAccount", "code": code, "response": response}

    if open_id is None or open_id == "":
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if account is None or len(account) < 8:
        code = "-1"
        error = "请输入VIP投资者代码"

    if open_name is None or open_name == "":
        code = "-1"
        error = "请输入姓名"
    elif len(open_name) > 20:
        code = "-1"
        error = "姓名超长"

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

    sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE investorid = %s AND investorstatus = '6' FOR UPDATE'''
    cursor.execute(sql, (account, ))
    row = cursor.fetchone()

    if row is None:
        sql = """SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investorid = %s AND investorstatus = '1'"""
        cursor.execute(sql, (open_id, account,))
        row = cursor.fetchone()

        if row is None:
            code = "-1"
            error = "暂无可用账户"

            response.update({"error": error})
            result.update({"code": code, "response": response})
        else:
            password = str(row[3])

            response.update({"account": account, "password": password})
            result.update({"response": response})
    else:
        password = str(row[3])

        sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s AND investorid != %s'''
        cursor.execute(sql, (open_id, account,))
        row = cursor.fetchone()

        if row is not None:
            sql = '''UPDATE siminfo.t_investor SET openid = CONCAT(openid, "_o") WHERE openid = %s AND investorid != %s'''
            cursor.execute(sql,(open_id, account,))

        sql = '''UPDATE siminfo.t_investor SET investorname = %s, openid = %s, investorstatus = '1' WHERE investorid = %s'''
        cursor.execute(sql, (open_name, open_id, account))

        if cursor.rowcount == 1:
            response.update({"account": account, "password": password})
            result.update({"response": response})
        else:
            code = "-1"
            error = "开户失败：更新投资者信息失败"

            response.update({"error": error})
            result.update({"code": code, "response": response})

    mysql_conn.commit()

    if code == "0" and activity is not None and activity != "":
        join_result = join_activity_with_account(mysql_conn, {"account": account, "activity": activity})

        if join_result.get("code") != "0":
            code = "-2"
            error = join_result.get("response").get("error")

            response.update({"error": error})
            result.update({"code": code, "response": response})

    return result


def join_activity(mysql_conn, parameters):
    open_id = parameters.get("id")
    activity = parameters.get("activity")

    code = "0"
    response = {"id": open_id, "activity": activity}
    result = {"kind": "joinActivity", "code": code, "response": response}

    if open_id is None or open_id == "":
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if activity is None or activity == "":
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

    open_result = open_account(mysql_conn, parameters)
    if open_result.get("code") != "0":
        code = "-2"
        response = open_result.get("response")
        result.update({"code": code, "response": response})
    else:
        response = open_result.get("response")
        result.update({"response": response})

    return result


def join_activity_with_account(mysql_conn, parameters):
    account = parameters.get("account")
    activity = parameters.get("activity")

    code = "0"
    response = {"account": account, "activity": activity}
    result = {"kind": "joinActivityWithAccount", "code": code, "response": response}

    if account is None or account == "":
        code = "-1"
        error = "请输入投资者代码"

    if activity is None or activity == "":
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

    sql = '''SELECT investorid FROM siminfo.t_investor WHERE investorid =  %s'''
    cursor.execute(sql, (account,))
    row = cursor.fetchone()

    if row is None:
            code = "-1"
            error = "投资者代码不存在"

            response.update({"error": error})
            result.update({"code": code, "response": response})
    else:
        investor_id = str(row[0])
        sql = '''SELECT activityid FROM siminfo.t_activity WHERE activityid =  %s AND activitystatus in ('0', '1')'''
        cursor.execute(sql, (activity,))
        row = cursor.fetchone()

        if row is None:
                code = "-1"
                error = "赛事活动不存在或已过期"

                response.update({"error": error})
                result.update({"code": code, "response": response})
        else:
            sql = '''SELECT activityid, investorid, joindate FROM siminfo.t_activityinvestor WHERE activityid =  %s AND investorid = %s'''
            cursor.execute(sql, (activity, investor_id))
            row = cursor.fetchone()

            if row is None:
                sql = """SELECT settlementgroupid FROM siminfo.t_activitysettlementgroup 
                                        WHERE activityid = %s AND settlementgroupid IN(
                                        SELECT DISTINCT settlementgroupid FROM siminfo.t_activitysettlementgroup t 
                                        WHERE t.activityid IN 
                                        (SELECT t1.activityid FROM siminfo.t_activityinvestor t1, siminfo.t_activity t2 
                                        WHERE t1.investorid = %s AND t1.activityid = t2.activityid AND t2.activitytype != '0' AND (t2.activitystatus = '0' OR t2.activitystatus = '1')))"""
                cursor.execute(sql, (activity, investor_id))
                cursor.fetchall()
                if cursor.rowcount > 0:
                    code = "-1"
                    error = "投资者已参加其他相似类型赛事活动"

                    response.update({"error": error})
                    result.update({"code": code, "response": response})
                else:
                    # 检查赛事活动状态
                    sql = """SELECT activitystatus, joinmode FROM siminfo.t_activity WHERE activityid = %s"""
                    cursor.execute(sql, (activity,))
                    row = cursor.fetchone()
                    activity_status = str(row[0])
                    join_mode = str(row[1])

                    join_status = '0'
                    # 检查投资者资金 持仓
                    if activity_status == '1':
                        sql = """SELECT t1.investorid FROM siminfo.t_investorfund t1
                                                    WHERE t1.brokersystemid IN (SELECT DISTINCT t2.brokersystemid 
                                                            FROM siminfo.t_activitysettlementgroup t1, siminfo.t_brokersystemsettlementgroup t2 WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.activityid = %s)
                                                        AND t1.investorid = %s AND (t1.currentasset <> t1.initialasset OR t1.preasset <> t1.initialasset OR t1.currmargin <> 0 OR t1.profit <> 0 OR t1.stockvalue <> 0)
                                                    UNION
                                                    SELECT DISTINCT t2.investorid FROM siminfo.t_clientposition t1, siminfo.t_investorclient t2, (SELECT settlementgroupid FROM siminfo.t_activitysettlementgroup WHERE activityid = %s) t3
                                                    WHERE t2.investorid = %s AND t1.clientid = t2.clientid AND t1.settlementgroupid = t2.settlementgroupid AND t2.settlementgroupid = t3.settlementgroupid AND t1.position > 0"""
                        cursor.execute(sql, (activity,investor_id,activity,investor_id))
                        cursor.fetchall()
                        if cursor.rowcount == 0 or join_mode == '0' or join_mode == '1':
                            sql = """INSERT INTO siminfo.t_activityinvestorevaluation(ActivityID,InvestorID,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,TotalReturnRate,ReturnRateOf1Day)
                                                SELECT t2.activityid, t1.investorid, SUM(t1.currentasset) AS initialasset, SUM(t1.premonthasset) AS premonthasset, SUM(t1.preweekasset) AS preweekasset, SUM(t1.preasset) AS preasset, SUM(t1.currentasset) AS currasset, 0, 0  FROM siminfo.t_investorfund t1,
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

    if activity_id is None or activity_id == "":
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
        sql = '''SELECT activityid FROM siminfo.t_activity WHERE activityid =  %s AND activitystatus in ('0', '1')'''
        cursor.execute(sql, (activity_id,))
        row = cursor.fetchone()

        if row is None:
                code = "-1"
                error = "赛事活动不存在或已过期"

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
