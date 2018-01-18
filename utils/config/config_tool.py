# -*- coding: UTF-8 -*-

import json
from utils.logger.log import log

log = log.get_logger(category="config")

def load(args):
    _merge_config = {}
    for f in args:
        jsonData = __getConfig(filename=f)
        log.info("loading config module ==> " + jsonData['name'])
        _merge_config[jsonData['name']] = jsonData['module']
    return _merge_config

# 获取config配置文件
def __getConfig(filename):
    f = open(filename)
    return json.load(f)
