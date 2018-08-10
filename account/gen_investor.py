# -*- coding: UTF-8 -*-

import csv
import os
from utils import Configuration, mysql, log, parse_conf_args, csv_tool, path


def gen_investors(context, conf):
    logger = log.get_logger(category="Investors")

    _mysql = mysql(configs=context.get("mysql")[conf.get("mysqlId")])

    User = dict(columns=("UserID", "Passwd"),
                sql="""select InvestorID, Password from siminfo.t_investor"""),
    csv_data = _mysql.select(User[0]['sql'])

    output = path.convert(context.get("csv")[conf.get("csv")]['quant'])
    if not os.path.exists(str(output)):
        os.makedirs(str(output))
    csv_path = os.path.join(output, "user.csv")
    produce_csv(User[0]["columns"], csv_data, csv_path)

# 生成csv文件
def produce_csv(columns, csv_data, _path):
    with open(_path, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_tool.covert_to_gbk(columns))
        writer.writerows(csv_tool.covert_to_gbk(csv_data))

def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "csv"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_investors(context, conf)


if __name__ == "__main__":
    main()
