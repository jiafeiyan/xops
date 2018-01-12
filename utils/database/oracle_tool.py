# -*- coding: UTF-8 -*-
import cx_Oracle

from utils.logger.log import log


class oracle:
    def __init__(self, configs=None):
        self.logger = log.get_logger("oracleDB", configs["Log"]["verbose"])
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

    def __getCnx(self):
        acq = self.pool.acquire()
        return acq

    def __releaseCnx(self, cnx):
        self.pool.release(cnx)

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
            self.__releaseCnx(cnx)

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
            self.__releaseCnx(cnx)

    # 批量执行
    def executemany(self, sql, params):
        cnx = self.__getCnx()
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
            self.__releaseCnx(cnx)
