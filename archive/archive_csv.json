{
    "Archives" : [{
        "host" : "stock_exchange",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/tinit/dump run/tkernel1/dump",
          "target" : "sysdatabackup/stock_exchange_csv_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "future_exchange",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/tinit/dump run/tkernel1/dump",
          "target" : "sysdatabackup/future_exchange_csv_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "stock_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/tinit/csv run/dbsync/dump",
          "target" : "sysdatabackup/stock_broker_csv_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "etf_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/sptinit/csv",
          "target" : "sysdatabackup/etf_broker_csv_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "future_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "tinit/perf",
          "target" : "sysdatabackup/future_broker_csv_`date +%Y%m%d`.tar.gz"
        }]
    }]
}
