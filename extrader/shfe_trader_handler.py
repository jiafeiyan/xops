#-*- coding: UTF-8 -*-

import thread
import threading
import Queue

import shfetraderapi

from xmq import xmq_puber
from utils import log


class SHFETraderHandler(shfetraderapi.CShfeFtdcTraderSpi):
    def __init__(self, trader_api, user_id, password):
        self.logger = log.get_logger(category="SHFETraderSpi")

        shfetraderapi.CShfeFtdcTraderSpi.__init__(self)

        self.trader_api = trader_api

        self.userId = user_id
        self.password = password

        self.is_connected = False
        self.is_logined = False

        self.request_id = 0
        self.lock = threading.Lock()

    def set_msg_puber(self, msg_puber):
        self.msg_puber = msg_puber

    def get_request_id(self):
        self.lock.acquire()
        self.request_id += 1
        req_id = self.request_id
        self.lock.release()
        return req_id

    def OnFrontConnected(self):
        self.logger.info("OnFrontConnected")
        self.is_connected = True

        req_login_field = shfetraderapi.CShfeFtdcReqUserLoginField()
        req_login_field.UserID = str(self.userId)
        req_login_field.Password = str(self.password)

        self.trader_api.ReqUserLogin(req_login_field, self.get_request_id())

    def OnFrontDisconnected(self, nReason):
        self.logger.info("OnFrontDisconnected: %s" % str(nReason))
        self.is_connected = False

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        self.logger.info("OnRspUserLogin")

        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("login failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            self.logger.info("login success")
            self.is_logined = True

    def OnRspQryInstrumentStatus(self, pInstrumentStatus, pRspInfo, nRequestID, bIsLast):
        self.logger.info("OnRspQryInstrumentStatus")

        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("login failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            print(pInstrumentStatus)
            if pInstrumentStatus is not None:
                self.logger.info("instrument[%s] current status is [%s]" % (pInstrumentStatus.InstrumentID, pInstrumentStatus.InstrumentStatus))
                msg = {"type": "istatus", "data": {"InstrumentID": pInstrumentStatus.InstrumentID, "InstrumentStatus": pInstrumentStatus.InstrumentStatus}}
                self.msg_puber.send(msg)

    def OnRtnInstrumentStatus(self, pInstrumentStatus):
        self.logger.info("OnRtnInstrumentStatus")

        if pInstrumentStatus is not None:
            self.logger.info("instrument[%s] current status is [%s]" % (pInstrumentStatus.InstrumentID, pInstrumentStatus.InstrumentStatus))
            msg = {"type": "istatus", "data": {"InstrumentID": pInstrumentStatus.InstrumentID, "InstrumentStatus": pInstrumentStatus.InstrumentStatus}}
            self.msg_puber.send(msg)




