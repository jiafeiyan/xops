# -*- coding: UTF-8 -*-

import threading
import shfetraderapi
import time
import os

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

        self.private_worker = False
        # 初始化锁文件【防止多进程重复擦送合约状态信息】
        try:
            os.mknod("private_worker.con", 0600)
            self.private_worker = True
        except OSError:
            pass

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
        req_login_field.TradingDay = str(self.tradingday)

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
            req_login_field.TradingDay = str(self.tradingday)
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
            if self.private_worker:
                self.msg_puber.send(msg)

    def control_md_status(self):
        self.lock.acquire()
        try:
            pass
        finally:
            self.lock.release()

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            self.logger.error("OnRspOrderInsert failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
        else:
            pass

    # def OnRspOrderAction(self, pOrderAction, pRspInfo, nRequestID, bIsLast):
    #     self.logger.info("OnRspOrderAction")
    #     if pRspInfo is not None and pRspInfo.ErrorID != 0:
    #         self.logger.error("OnRspOrderAction failed : %s" % pRspInfo.ErrorMsg.decode("GBK").encode("UTF-8"))
    #     else:
    #         if pOrderAction is not None:
    #             msg = {
    #                 "OrderSysID": pOrderAction.OrderSysID,
    #                 "OrderLocalID": pOrderAction.OrderLocalID,
    #                 "ActionFlag": pOrderAction.ActionFlag,
    #                 "ParticipantID": pOrderAction.ParticipantID,
    #                 "ClientID": pOrderAction.ClientID,
    #                 "UserID": pOrderAction.UserID,
    #                 "LimitPrice": pOrderAction.LimitPrice,
    #                 "VolumeChange": pOrderAction.VolumeChange,
    #                 "ActionLocalID": pOrderAction.ActionLocalID,
    #                 "BusinessUnit": pOrderAction.BusinessUnit,
    #                 "BusinessLocalID": pOrderAction.BusinessLocalID
    #             }
    #             print msg

    def OnRtnOrder(self, pOrder):
        self.logger.info("OnRtnOrder")
        if pOrder is not None:
            data = {
                "TradingDay": pOrder.TradingDay,
                # "SettlementGroupID": pOrder.SettlementGroupID,
                # "SettlementID": pOrder.SettlementID,
                "OrderSysID": pOrder.OrderSysID,
                "ParticipantID": pOrder.ParticipantID,
                "ClientID": pOrder.ClientID,
                # "UserID": pOrder.UserID,
                # "InstrumentID": pOrder.InstrumentID,
                # "OrderPriceType": pOrder.OrderPriceType,
                # "Direction": pOrder.Direction,
                # "CombOffsetFlag": pOrder.CombOffsetFlag,
                # "CombHedgeFlag": pOrder.CombHedgeFlag,
                # "LimitPrice": pOrder.LimitPrice,
                # "VolumeTotalOriginal": pOrder.VolumeTotalOriginal,
                # "TimeCondition": pOrder.TimeCondition,
                # "GTDDate": pOrder.GTDDate,
                # "VolumeCondition": pOrder.VolumeCondition,
                # "MinVolume": pOrder.MinVolume,
                # "ContingentCondition": pOrder.ContingentCondition,
                # "StopPrice": pOrder.StopPrice,
                # "ForceCloseReason": pOrder.ForceCloseReason,
                # "OrderLocalID": pOrder.OrderLocalID,
                # "IsAutoSuspend": pOrder.IsAutoSuspend,
                # "OrderSource": pOrder.OrderSource,
                "OrderStatus": pOrder.OrderStatus,
                # "OrderType": pOrder.OrderType,
                # "VolumeTraded": pOrder.VolumeTraded,
                # "VolumeTotal": pOrder.VolumeTotal,
                # "InsertDate": pOrder.InsertDate,
                # "InsertTime": pOrder.InsertTime,
                # "ActiveTime": pOrder.ActiveTime,
                # "SuspendTime": pOrder.SuspendTime,
                # "UpdateTime": pOrder.UpdateTime,
                # "CancelTime": pOrder.CancelTime,
                # "ActiveUserID": pOrder.ActiveUserID,
                # "Priority": pOrder.Priority,
                # "TimeSortID": pOrder.TimeSortID,
                # "ClearingPartID": pOrder.ClearingPartID,
                # "BusinessUnit": pOrder.BusinessUnit,
                # "BusinessLocalID": pOrder.BusinessLocalID,
                # "ActionDay": pOrder.ActionDay,
            }
            msg = {"type": "rtnOrder",
                   "data": [pOrder.TradingDay,
                            pOrder.OrderSysID,
                            pOrder.ParticipantID,
                            pOrder.ClientID,
                            pOrder.OrderStatus]}
            self.msg_puber.send(msg)

    def OnRtnTrade(self, pTrade):
        self.logger.info("OnRtnTrade")
        if pTrade is not None:
            data = {
                "TradingDay": pTrade.TradingDay,
                # "SettlementGroupID": pTrade.SettlementGroupID,
                # "SettlementID": pTrade.SettlementID,
                # "TradeID": pTrade.TradeID,
                # "Direction": pTrade.Direction,
                "OrderSysID": pTrade.OrderSysID,
                "ParticipantID": pTrade.ParticipantID,
                "ClientID": pTrade.ClientID,
                # "TradingRole": pTrade.TradingRole,
                # "AccountID": pTrade.AccountID,
                # "InstrumentID": pTrade.InstrumentID,
                # "OffsetFlag": pTrade.OffsetFlag,
                # "HedgeFlag": pTrade.HedgeFlag,
                # "Price": pTrade.Price,
                # "Volume": pTrade.Volume,
                # "TradeTime": pTrade.TradeTime,
                # "TradeType": pTrade.TradeType,
                # "PriceSource": pTrade.PriceSource,
                # "UserID": pTrade.UserID,
                # "OrderLocalID": pTrade.OrderLocalID,
                # "ClearingPartID": pTrade.ClearingPartID,
                # "BusinessUnit": pTrade.BusinessUnit,
                # "BusinessLocalID": pTrade.BusinessLocalID,
                # "ActionDay": pTrade.ActionDay,
            }
            msg = {"type": "rtnTrade",
                   "data": [pTrade.TradingDay,
                            pTrade.OrderSysID,
                            pTrade.ParticipantID,
                            pTrade.ClientID]}
            self.msg_puber.send(msg)
