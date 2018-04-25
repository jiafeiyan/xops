# -*- coding: UTF-8 -*-

import threading
import shfemdapi

from utils import log


class MdHandler(shfemdapi.CShfeFtdcMduserSpi):
    def __init__(self, md_api, user_id, password):
        self.logger = log.get_logger(category="MdSpi")

        shfemdapi.CShfeFtdcMduserSpi.__init__(self)

        self.md_api = md_api

        self.userId = user_id
        self.password = password

        self.is_connected = False
        self.is_logined = False

        self.request_id = 0
        self.lock = threading.Lock()

    def set_msg_puber(self, msg_puber):
        self.msg_puber = msg_puber

    def OnFrontConnected(self):
        self.logger.info("OnFrontConnected")
        self.is_connected = True

        req_login_field = shfemdapi.CShfeFtdcReqUserLoginField()
        req_login_field.UserID = str(self.userId)
        req_login_field.Password = str(self.password)

        self.md_api.ReqUserLogin(req_login_field, self.get_request_id())

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

    def OnRspSubscribeTopic(self, pDissemination, pRspInfo, nRequestID, bIsLast):
        self.logger.info("OnRspSubscribeTopic")
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("OnRspSubscribeTopic failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            print("SequenceSeries ==> " + str(pDissemination.SequenceSeries))
            print("SequenceNo ==> " + str(pDissemination.SequenceNo))

    def OnRtnDepthMarketData(self, pDepthMarketData):
        self.logger.info("OnRtnDepthMarketData")
        if pDepthMarketData is not None:
            InstrumentID = pDepthMarketData.InstrumentID
            LastPrice = pDepthMarketData.LastPrice
            msg = {"type": "marketdata", "data": {InstrumentID: {"InstrumentID": InstrumentID, "LastPrice": LastPrice}}}
            self.msg_puber.send(msg)

    def get_request_id(self):
        self.lock.acquire()
        self.request_id += 1
        req_id = self.request_id
        self.lock.release()
        return req_id