# -*- coding: UTF-8 -*-

import json
import Queue
import sys
import csv
import os
import threading
import time
import random
from datetime import datetime

from msg_resolver_qry_insstatus import QryInstrumentStatusMsgResolver
from xmq import xmq_pusher, xmq_resolving_suber, xmq_msg_resolver, xmq_resolving_puller
from utils import Configuration, parse_conf_args, log, path

def order_record(context, conf):
    pass


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["exchange", "xmq"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files,
                                       add_ons=add_ons)

    order_record(context, conf)


if __name__ == "__main__":
    main()
