#-*- coding: UTF-8 -*-
import uuid
import json
import mysql.connector

from activity_handler import join_activity
from account_handler import open_account


def test_account():
    config = eval("{'user':'siminfo', 'password':'111111', 'host':'127.0.0.1', 'database':'siminfo'}")
    conn = mysql.connector.connect(**config)
    conn.set_charset_collation('utf8')
    print(json.dumps(open_account(conn, {"id": "11111111112", "name": "测试", "activity": "0002"}), encoding="UTF-8", ensure_ascii=False))


def test_activity():
    config = eval("{'user':'siminfo', 'password':'111111', 'host':'127.0.0.1', 'database':'siminfo'}")
    conn = mysql.connector.connect(**config)
    conn.set_charset_collation('utf8')
    print(json.dumps(join_activity(conn, {"id": "11111111111", "activity": "0001"}), encoding="UTF-8", ensure_ascii=False))


if __name__ == "__main__":
    print("1".rjust(8, "0"))
    print(uuid.uuid4())