# -*- coding: UTF-8 -*-

import os
import json

class Configuration:
    @staticmethod
    def load(base_dir, config_names, config_files):
        context = {}
        conf = {}

        config_base_dir = base_dir

        if config_base_dir is None:
            config_base_dir = os.environ.get("SIM_PLATFORM_HOME", None)
            config_base_dir += "\configuration"

        if config_base_dir is not None and config_names is not None:
            for config_name in config_names:
                config_file = os.path.join(config_base_dir, config_name + ".json")

                context.update({config_name: Configuration.load_json(config_file)})

        if config_files is not None:
            for config_file in config_files:
                if config_file is not None and os.path.exists(config_file):
                    conf.update(Configuration.load_json(config_file))

        return context, conf

    @staticmethod
    def find_selfconfig(file_name):
        self_config_file = file_name[:-3] + ".json"
        if os.path.exists(self_config_file):
            return self_config_file
        return None

    @staticmethod
    def load_json(file_name):
        f = open(file_name)

        config = json.load(f)

        return config
