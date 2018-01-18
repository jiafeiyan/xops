# -*- coding: UTF-8 -*-
import cx_Oracle

from utils.logger.log import log


class oracle:
    def __init__(self, configs):
        if "Log" in configs:
            self.logger = log.get_logger(category="oracle",
                                         file_Path=configs["Log"]["file_path"],
                                         console_level=configs["Log"]["console_level"],
                                         file_level=configs["Log"]["file_level"])
        else:
            self.logger = log.get_logger(category="oracle")

        _user = configs["Oracle"]["user"]
        _password = configs["Oracle"]["password"]
        _host = configs["Oracle"]["host"]
        _port = configs["Oracle"]["port"]
        _sid = configs["Oracle"]["sid"]
        _min = configs["Oracle"]["pool_min"]
        _max = configs["Oracle"]["pool_max"]
        self.__connect(_user, _password, _host, _port, _sid, _min, _max)

    def __connect(self, user, password, host, port, sid, _min, _max):
        dsn = cx_Oracle.makedsn(host, port, sid)
        self.logger.info("start connect oracle database [ user=%s, host=%s, port=%s ]", user, host, port)
        self.pool = cx_Oracle.SessionPool(user=user, password=password, dsn=dsn, min=_min, max=_max, increment=1)

    def get_cnx(self):
        acq = self.pool.acquire()
        return acq

    def __release_cnx(self, cnx):
        self.pool.release(cnx)

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
            self.__release_cnx(cnx)

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
            self.__release_cnx(cnx)

    # 批量执行
    def executemany(self, sql, params):
        cnx = self.get_cnx()
        try:
            self.logger.debug({"sql": sql, "params": params})
            cursor = cnx.cursor()
            cursor.prepare(sql)
            cursor.executemany(None, params)
            cnx.commit()
        except Exception as err:
            cnx.rollback()
            self.logger.error(err)
        finally:
            cursor.close()
            self.__release_cnx(cnx)
