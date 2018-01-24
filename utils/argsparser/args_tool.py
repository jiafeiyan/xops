# -*- coding: UTF-8 -*-

import argparse

from utils.config.config_tool import Configuration


def parse_conf_args(file_name, base_dir=None, config_names=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-base')
    parser.add_argument('-imp', nargs='+')
    parser.add_argument('-conf', nargs='+')
    args = parser.parse_args()
    if args.conf is None:
        args.conf = []

    args.conf.insert(0, Configuration.find_selfconfig(file_name))

    return base_dir if args.base is None else args.base, config_names if args.imp is None else args.imp, args.conf
