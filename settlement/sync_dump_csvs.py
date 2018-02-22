# -*- coding: UTF-8 -*-

import os
import json

import rsync
from utils import log, Configuration, parse_conf_args, process_assert


def sync_dump_csvs(context, conf):
    result_code = 0
    logger = log.get_logger(category="SyncDumpCsvs")

    trade_system_id = conf.get("tradeSystemId")
    settlement_id = conf.get("settlementId")

    base_dir = conf.get("baseDataHome")

    data_target_dir = os.path.join(base_dir, trade_system_id, settlement_id)

    rsync_config = {"type": "get", "target": data_target_dir, "Syncs": conf.get("Syncs")}
    logger.info("[sync dump csvs with %s] begin" % json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False))
    try:
        rsync.rsync_groups(context, rsync_config)
    except Exception as e:
        logger.info("[sync dump csvs with %s] Error: %s" % (json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False), e))
        result_code = -1

    logger.info("[sync dump csvs with %s] end" % json.dumps(rsync_config, encoding="UTF-8", ensure_ascii=False))
    return result_code

def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["hosts"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(sync_dump_csvs(context, conf))


if __name__ == "__main__":
    main()