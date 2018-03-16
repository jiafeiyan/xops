#-*- coding: UTF-8 -*-

import sys
import json

import tornado.ioloop
import tornado.web
import tornado.log

from account_handler import open_account
from activity_handler import join_activity, query_activity_ranking, query_activity_joinstatus

from utils import Configuration, mysql, parse_conf_args, log


class OpenAccountHandler(tornado.web.RequestHandler):
    def initialize(self, database, logger):
        self.database = database
        self.logger = logger

    def get(self):
        return self.do_service()

    def post(self):
        return self.do_service()

    def do_service(self):
        open_id = self.get_argument("id", None)
        open_name = self.get_argument("name", None)
        activity_id = self.get_argument("activity", None)

        result = {"kind": "openAccount", "code": "-1", "response": {"id": open_id, "activity": activity_id, "error": "系统内部错误"}}

        self.logger.info("openAccount begin [ id=%s, name=%s, activity=%s ]", open_id, open_name, activity_id)

        conn = self.database.get_cnx()
        try:
            result = open_account(conn, {"id": open_id, "name":  open_name, "activity": activity_id})
        except:
            self.logger.error(sys.exc_info()[0])
        finally:
            conn.close()

        result_json = json.dumps(result, encoding="UTF-8", ensure_ascii=False)
        self.set_header("Content-Type", "text/json;charset=UTF-8")
        self.write(result_json)

        self.logger.info("openAccount end [ result= %s ]", result_json)


class JoinActivityHandler(tornado.web.RequestHandler):
    def initialize(self, database, logger):
        self.database = database
        self.logger = logger

    def get(self):
        return self.do_service()

    def post(self):
        return self.do_service()

    def do_service(self):
        open_id = self.get_argument("id", None)
        activity_id = self.get_argument("activity", None)

        self.logger.info("joinActivity begin [ id=%s, activity=%s ]", open_id, activity_id)

        result = {"kind": "joinActivity", "code": "-1", "response": {"id": open_id, "activity": activity_id, "error": "系统内部错误"}}

        conn = self.database.get_cnx()
        try:
            result = join_activity(conn, {"id": open_id, "activity": activity_id})
        except:
            self.logger.error(sys.exc_info()[0])
        finally:
            conn.close()

        result_json = json.dumps(result, encoding="UTF-8", ensure_ascii=False)
        self.set_header("Content-Type", "text/json;charset=UTF-8")
        self.write(result_json)

        self.logger.info("joinActivity end [ result= %s ]", result_json)


class QueryActivityRankingHandler(tornado.web.RequestHandler):
    def initialize(self, database, logger):
        self.database = database
        self.logger = logger

    def get(self):
        return self.do_service()

    def post(self):
        return self.do_service()

    def do_service(self):
        activity_id = self.get_argument("activity", None)
        investor_id = self.get_argument("investor", None)
        query_type = self.get_argument("type", "00")
        query_count = int(self.get_argument("count", "0"))

        self.logger.info("queryActivityRanking begin [ activity=%s, investor=%s, type=%s, count=%d ]", activity_id, investor_id, query_type, query_count)

        result = {"kind": "queryActivityRanking", "code": "-1", "response": {"activity": activity_id, "investor": investor_id, "type": query_type, "count": query_count, "error": "系统内部错误"}}

        conn = self.database.get_cnx()
        try:
            result = query_activity_ranking(conn, {"activity": activity_id, "investor": investor_id, "type": query_type, "count": query_count})
        except:
            self.logger.error(sys.exc_info()[0])
        finally:
            conn.close()

        result_json = json.dumps(result, encoding="UTF-8", ensure_ascii=False)
        self.set_header("Content-Type", "text/json;charset=UTF-8")
        self.write(result_json)

        self.logger.info("queryActivityRanking end [ result= %s ]", result_json)


class QueryActivityJoinStatusHandler(tornado.web.RequestHandler):
    def initialize(self, database, logger):
        self.database = database
        self.logger = logger

    def get(self):
        return self.do_service()

    def post(self):
        return self.do_service()

    def do_service(self):
        activity_id = self.get_argument("activity", None)
        open_id = self.get_argument("id", None)

        self.logger.info("queryActivityJoinStatus begin [ activity=%s, id=%s]", activity_id, open_id)

        result = {"kind": "queryActivityJoinStatus", "code": "-1", "response": {"activity": activity_id, "id": open_id, "error": "系统内部错误"}}

        conn = self.database.get_cnx()
        try:
            result = query_activity_joinstatus(conn, {"activity": activity_id, "id": open_id})
        except:
            self.logger.error(sys.exc_info()[0])
        finally:
            conn.close()

        result_json = json.dumps(result, encoding="UTF-8", ensure_ascii=False)
        self.set_header("Content-Type", "text/json;charset=UTF-8")
        self.write(result_json)

        self.logger.info("queryActivityJoinStatus end [ result= %s ]", result_json)


def start_http_server(context, conf):
    logger = log.get_logger(category="HttpServer")

    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    app = tornado.web.Application([
        (r"/openAccount", OpenAccountHandler, dict(database=mysql_pool, logger=logger)),
        (r"/joinActivity", JoinActivityHandler, dict(database=mysql_pool, logger=logger)),
        (r"/queryActivityRanking", QueryActivityRankingHandler, dict(database=mysql_pool, logger=logger)),
        (r"/queryActivityJoinStatus", QueryActivityJoinStatusHandler, dict(database=mysql_pool, logger=logger)),
    ])
    app.listen(conf["port"])

    tornado.ioloop.IOLoop.current().start()


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    start_http_server(context, conf)


if __name__ == "__main__":
    main()