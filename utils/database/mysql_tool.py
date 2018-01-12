# -*- coding: UTF-8 -*-

from utils.logger.log import log
from mysql.connector import pooling


class mysql:
    def __init__(self, configs=None):
        self.logger = log.get_logger("mysqlDB", configs["Log"]["verbose"])
        dbConfig = {
            "user": configs["MySQL"]["user"],
            "password": configs["MySQL"]["password"],
            "host": configs["MySQL"]["host"],
            "port": configs["MySQL"]["port"],
            "database": configs["MySQL"]["database"]
        }
        self.__connect(dbConfig=dbConfig, pool_size=configs["MySQL"]["pool_size"])

    def __connect(self, dbConfig, pool_size):
        self.pool = pooling.MySQLConnectionPool(pool_size=pool_size, **dbConfig)
        self.logger.info("start connect mysql database [ user=%s, host=%s, port=%s ]",
                         dbConfig["user"], dbConfig["host"], dbConfig["port"])

    def __getCnx(self):
        return self.pool.get_connection()

    # 查询
    def select(self, sql, params=None):
        cnx = self.__getCnx()
        try:
            self.logger.debug({"sql": sql, "params": params})
            cursor = cnx.cursor()
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            fc = cursor.fetchall()
            return fc
        except Exception as err:
            self.logger.error(err)
        finally:
            cursor.close()
            cnx.close()

    # 执行
    def execute(self, sql, params=None):
        cnx = self.__getCnx()
        try:
            self.logger.debug({"sql": sql, "params": params})
            cursor = cnx.cursor()
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            cnx.commit()
        except Exception as err:
            self.logger.error(err)
        finally:
            cursor.close()
            cnx.close()

    # 批量执行
    def executemany(self, sql, params):
        cnx = self.__getCnx()
        try:
            self.logger.debug({"sql": sql, "params": params})
            cursor = cnx.cursor()
            cursor.executemany(sql, params)
            cnx.commit()
        except Exception as err:
            cnx.rollback()
            self.logger.error(err)
        finally:
            cursor.close()
            cnx.close()
