# -*- coding: UTF-8 -*-

from utils.logger.log import log
from mysql.connector import pooling


class mysql:
    def __init__(self, configs):
        if "Log" in configs:
            self.logger = log.get_logger(category="mysql",
                                         file_Path=configs["Log"]["file_path"],
                                         console_level=configs["Log"]["console_level"],
                                         file_level=configs["Log"]["file_level"])
        else:
            self.logger = log.get_logger(category="mysql")
        db_config = {
            "user": configs["MySQL"]["user"],
            "password": configs["MySQL"]["password"],
            "host": configs["MySQL"]["host"],
            "port": configs["MySQL"]["port"],
            "database": configs["MySQL"]["database"]
        }
        self.__connect(db_config=db_config, pool_size=configs["MySQL"]["pool_size"])

    def __connect(self, db_config, pool_size):
        self.pool = pooling.MySQLConnectionPool(pool_size=pool_size, **db_config)
        self.logger.info("start connect mysql database [ user=%s, host=%s, port=%s ]",
                         db_config["user"], db_config["host"], db_config["port"])

    def get_cnx(self):
        return self.pool.get_connection()

    # 判断是否存在记录
    def is_exist(self, sql, params):
        res = self.select(sql=sql, params=params)
        if len(res) > 0:
            return True
        else:
            return False

    # 查询
    def select(self, sql, params=None):
        cnx = self.get_cnx()
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
        cnx = self.get_cnx()
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
        cnx = self.get_cnx()
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
