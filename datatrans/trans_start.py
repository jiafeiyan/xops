# -*- coding: UTF-8 -*-

import trans_stockinfo
import trans_futureinfo

def init(mysql):
    parameters = {
        'SettlementGroupID': 'SG01',
        'ProductID': 'Share5',
        'ProductGroupID': 'ShareX05',
        'VolumeMultiple': 1
    }
    # trans_stockinfo.transform(param=parameters, mysql=mysql)
    trans_futureinfo.transform(param=parameters, mysql=mysql)
