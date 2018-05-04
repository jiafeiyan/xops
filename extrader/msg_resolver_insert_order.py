#-*- coding: UTF-8 -*-

from trader_msg_resolver import TraderMsgResolver
import shfetraderapi

class InsertOrderMsgResolver(TraderMsgResolver):
    def __init__(self, handler):
        TraderMsgResolver.__init__(self, handler)

    def resolve_msg(self, msg):
        if msg is None or msg.get("type") is None or msg.get("ProductClass") is None:
            return -1

        type = msg.get("type")
        ProductClass = msg.get("ProductClass")
        if type == "order":
            data = msg.get("data")
            user = self.handler.userId
            input_order_field = shfetraderapi.CShfeFtdcInputOrderField()
            input_order_field.BusinessUnit = str(user)
            input_order_field.UserID = str(user)
            input_order_field.ClientID = str(data.get("ClientID"))
            input_order_field.ParticipantID = str(data.get("ParticipantID"))
            input_order_field.InstrumentID = str(data.get("InstrumentID"))
            input_order_field.LimitPrice = data.get("LimitPrice")
            input_order_field.VolumeTotalOriginal = data.get("VolumeTotalOriginal")
            input_order_field.Direction = data.get("Direction")
            input_order_field.OrderLocalID = ''
            input_order_field.MinVolume = 1
            input_order_field.CombOffsetFlag = '0'
            input_order_field.CombHedgeFlag = '1'
            input_order_field.IsAutoSuspend = 0
            input_order_field.TimeCondition = ord('3')
            # 限价 SHFE_FTDC_OPT_LimitPrice 2
            input_order_field.OrderPriceType = ord('2')
            # 任何数量 SHFE_FTDC_VC_AV '1'
            input_order_field.VolumeCondition = ord('1')
            # 立即SHFE_FTDC_CTC_Immediately ‘1’
            input_order_field.ContingentCondition = ord('1')
            # 非强平SHFE_FTDC_FCC_NotForceClose '0'
            input_order_field.ForceCloseReason = ord('0')
            request_id = self.handler.get_request_id()
            # 期货设置平开仓属性
            if ProductClass != "4":
                # 0 开仓 1 平仓
                input_order_field.CombOffsetFlag = '0'
            self.handler.trader_api.ReqOrderInsert(input_order_field, request_id)
            return 0
