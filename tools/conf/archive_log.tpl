{
    "Archives" : [{
        "host" : "stock_exchange",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/arb/log/*.log.* run/front1/log/*.log.* run/mdfront1/log/*.log.* run/qkernel1/log/*.log.* run/tinit/log/*.log.* run/tkernel1/log/*.log.* run/mdimport/log/*.log.* run/mdreceiver/log/*.log.*",
          "target" : "sysdatabackup/stock_exchange_log_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "future_exchange",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/arb/log/*.log.* run/front1/log/*.log.* run/mdfront1/log/*.log.* run/qkernel1/log/*.log.* run/tinit/log/*.log.* run/tkernel1/log/*.log.* run/mdimport/log/*.log.* run/mdreceiver/log/*.log.*",
          "target" : "sysdatabackup/future_exchange_log_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "stock_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/dbsync/log/*.log.* run/hx_adapter/log/*.log.* run/ssecffexmdserver/log/*.log.* run/ssecffexoffer/log/*.log.* run/szsecffexmdserver/log/*.log.* run/szsecffexoffer/log/*.log.* run/tinit/log/*.log.* run/tradeserver/log/*.log.*",
          "target" : "sysdatabackup/stock_broker_log_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "etf_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "run/ssecffexspmdoffer/log/*.log.* run/ssecffexspoffer/log/*.log.* run/sptinit/log/*.log.* run/sptradeserver/log/*.log.*",
          "target" : "sysdatabackup/etf_broker_log_`date +%Y%m%d`.tar.gz"
        }]
    },
    {
        "host" : "future_broker",
        "items" : [{
          "basedir" :"${HOME}",
          "sources" : "compositor1/log/*.log.* arb/log/*.log.* tkernel1/log/*.log.* qkernel1/log/*.log.* offermanager1/log/*.log.* front1/log/*.log.* front2/log/*.log.* tinit/log/*.log.* dceoffer1/log/*.log.* dcemdserver1/log/*.log.* zceoffer1/log/*.log.* zcemdserver1/log/*.log.* shfeoffer1/log/*.log.* shfemdserver1/log/*.log.* cffexoffer1/log/*.log.* ffexmdserver1/log/*.log.*",
          "target" : "sysdatabackup/future_broker_log_`date +%Y%m%d`.tar.gz"
        }]
    }]
}
