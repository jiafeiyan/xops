#-*- coding: UTF-8 -*-

import re
from activity_handler import join_activity

open_id_pattern = re.compile("^\d{11}$")


def open_account(mysql_conn, parameters):
    open_id = parameters.get("id")
    open_name = parameters.get("name")
    activity = parameters.get("activity")

    code = "0"
    response = {"id": open_id, "activity": activity}
    result = {"kind": "openAccount", "code": code, "response": response}

    if open_id is None:
        code = "-1"
        error = "请输入手机号"
    elif not open_id_pattern.match(open_id):
        code = "-1"
        error = "手机号格式错误"

    if open_name is None:
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

    sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE investorstatus = '0' ORDER BY investorid LIMIT 1 FOR UPDATE'''
    cursor.execute(sql)
    row = cursor.fetchone()

    if row is None:
        sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s'''
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

        sql = '''SELECT investorid, investorname, openid, PASSWORD, investorstatus FROM siminfo.t_investor WHERE openid = %s'''
        cursor.execute(sql, (open_id,))
        row = cursor.fetchone()

        if row is not None:
            account = str(row[0])
            password = str(row[3])

            response.update({"account": account, "password": password})
            result.update({"response": response})
        else:
            sql = '''UPDATE siminfo.t_investor SET investorname = %s, openid = %s, investorstatus = '1' WHERE investorid = %s'''
            cursor.execute(sql,(open_name, open_id, account))

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
        join_result = join_activity(mysql_conn, {"id": open_id, "activity": activity})

        if join_result.get("code") != "0":
            code = "-2"
            error = join_result.get("response").get("error")

            response.update({"error": error})
            result.update({"code": code, "response": response})

    return result