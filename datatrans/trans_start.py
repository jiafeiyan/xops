# -*- coding: UTF-8 -*-

import trans_stockinfo
import trans_futureinfo

def init(mysql, config):
    parameters = {
    }
    trans_stockinfo.transform(mysql=mysql, config=config)

    parameters = {
    }
    # trans_futureinfo.transform(mysql=mysql, config=config)
