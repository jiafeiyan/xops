# -*- coding: UTF-8 -*-

from utils import Configuration, parse_conf_args, rsync

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["hosts"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    rsync.rsync_groups(context, conf)


if __name__ == "__main__":
    main()
