# -*- coding: UTF-8 -*-

import threading
import shfemdapi
import time

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

    def set_msg_puber(self, msg_pusher):
        self.msg_pusher = msg_pusher

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
            time.sleep(3)
            req_login_field = shfemdapi.CShfeFtdcReqUserLoginField()
            req_login_field.UserID = str(self.userId)
            req_login_field.Password = str(self.password)
            self.md_api.ReqUserLogin(req_login_field, self.get_request_id())
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
            md_info = dict({"InstrumentID": pDepthMarketData.InstrumentID,
                            "LastPrice": float(pDepthMarketData.LastPrice),
                            "UpperLimitPrice": float(pDepthMarketData.UpperLimitPrice),
                            "LowerLimitPrice": float(pDepthMarketData.LowerLimitPrice),
                            "Volume": float(pDepthMarketData.Volume),
                            "BidPrice1": float(pDepthMarketData.BidPrice1),
                            "BidVolume1": float(pDepthMarketData.BidVolume1),
                            "AskPrice1": float(pDepthMarketData.AskPrice1),
                            "AskVolume1": float(pDepthMarketData.AskVolume1),
                            "BidPrice2": float(pDepthMarketData.BidPrice2),
                            "BidVolume2": float(pDepthMarketData.BidVolume2),
                            "AskPrice2": float(pDepthMarketData.AskPrice2),
                            "AskVolume2": float(pDepthMarketData.AskVolume2),
                            "BidPrice3": float(pDepthMarketData.BidPrice3),
                            "BidVolume3": float(pDepthMarketData.BidVolume3),
                            "AskPrice3": float(pDepthMarketData.AskPrice3),
                            "AskVolume3": float(pDepthMarketData.AskVolume3),
                            "BidPrice4": float(pDepthMarketData.BidPrice4),
                            "BidVolume4": float(pDepthMarketData.BidVolume4),
                            "AskPrice4": float(pDepthMarketData.AskPrice4),
                            "AskVolume4": float(pDepthMarketData.AskVolume4),
                            "BidPrice5": float(pDepthMarketData.BidPrice5),
                            "BidVolume5": float(pDepthMarketData.BidVolume5),
                            "AskPrice5": float(pDepthMarketData.AskPrice5),
                            "AskVolume5": float(pDepthMarketData.AskVolume5)})
            msg = {"type": "marketdata",
                   "data": {pDepthMarketData.InstrumentID: md_info}}
            self.msg_pusher.send(msg)

    def get_request_id(self):
        self.lock.acquire()
        self.request_id += 1
        req_id = self.request_id
        self.lock.release()
        return req_id