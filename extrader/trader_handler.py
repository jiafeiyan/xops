# -*- coding: UTF-8 -*-

import threading
import shfetraderapi
import time

from utils import log


class TraderHandler(shfetraderapi.CShfeFtdcTraderSpi):
    def __init__(self, trader_api, user_id, password, tradingday):
        self.logger = log.get_logger(category="TraderSpi")

        shfetraderapi.CShfeFtdcTraderSpi.__init__(self)

        self.trader_api = trader_api

        self.userId = user_id
        self.password = password
        self.tradingday = tradingday

        self.is_connected = False
        self.is_logined = False

        self.cache_md_status = dict()

        self.request_id = 0
        self.lock = threading.Lock()

    def set_msg_puber(self, msg_puber):
        self.msg_puber = msg_puber

    def send_status(self):
        for md in self.cache_md_status:
            self.msg_puber.send({"type": "istatus", "data": {md: self.cache_md_status.get(md)}})

    def get_request_id(self):
        self.lock.acquire()
        self.request_id += 1
        req_id = self.request_id
        self.lock.release()
        return req_id

    def ReqQryInstrumentStatus(self):
        req_status_field = shfetraderapi.CShfeFtdcQryInstrumentStatusField()
        self.trader_api.ReqQryInstrumentStatus(req_status_field, self.get_request_id())

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
            time.sleep(3)
            req_login_field = shfetraderapi.CShfeFtdcReqUserLoginField()
            req_login_field.UserID = str(self.userId)
            req_login_field.Password = str(self.password)
            req_login_field.TradingDay = str(self.TradingDay)
            self.trader_api.ReqUserLogin(req_login_field, self.get_request_id())

        else:
            self.logger.info("login success")
            self.is_logined = True

    def OnRspQryInstrumentStatus(self, pInstrumentStatus, pRspInfo, nRequestID, bIsLast):
        self.logger.info("OnRspQryInstrumentStatus")

        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("login failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            if pInstrumentStatus is not None:
                self.logger.info("instrument[%s] current status is [%s]" % (
                    pInstrumentStatus.InstrumentID, pInstrumentStatus.InstrumentStatus))
                msg = {"type": "istatus", "data": {
                    pInstrumentStatus.InstrumentID: {"InstrumentID": pInstrumentStatus.InstrumentID,
                                                     "InstrumentStatus": pInstrumentStatus.InstrumentStatus}}}
                self.cache_md_status.update(msg.get("data"))
                self.msg_puber.send(msg)

    def OnRtnInstrumentStatus(self, pInstrumentStatus):
        self.logger.info("OnRtnInstrumentStatus")

        if pInstrumentStatus is not None:
            self.logger.info("instrument[%s] current status is [%s]" % (
                pInstrumentStatus.InstrumentID, pInstrumentStatus.InstrumentStatus))
            msg = {"type": "istatus", "data": {
                pInstrumentStatus.InstrumentID: {"InstrumentID": pInstrumentStatus.InstrumentID,
                                                 "InstrumentStatus": pInstrumentStatus.InstrumentStatus}}}
            self.cache_md_status.update(msg.get("data"))
            self.msg_puber.send(msg)

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("OnRspOrderInsert failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            pass
