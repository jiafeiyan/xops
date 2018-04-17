# -*- coding: UTF-8 -*-

import sys

from utils import  Configuration, parse_conf_args, rshell


def clear_after_archive(context, conf):
    hosts_config = context.get("hosts")

    archive_configs = conf.get("Archives")

    for archive_config in archive_configs:
        host_id = archive_config.get("host")
        host_config = hosts_config.get(host_id)

        rsh = rshell(host_config)
        rsh.connect()

        items = archive_config.get("items")
        for item in items:
            base_dir = item.get("basedir", None)
            if base_dir is not None:
                stdin, stdout, stderr = rsh.execute("cd %s" % (base_dir,))
                error = stderr.read()
                if error is not "":
                    sys.stderr.write("Error: %s\n" % (error,))

            source_files_str = item.get("sources")
            target_file_str = item.get("target")

            stdin, stdout, stderr = rsh.execute("rm -rf %s" %(source_files_str,))
            error = stderr.read()
            if error is not "":
                sys.stderr.write("Error: %s\n" % (error,))

        rsh.disconnect()



def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["hosts"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    clear_after_archive(context, conf)


if __name__ == "__main__":
    main()
