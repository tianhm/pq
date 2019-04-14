#encoding:utf-8
import shelve
# accnf = 'meyzym.ac'
# accnf = 'dhqh.ac'
# accnf = 'hengtaiqh.ac'
# accnf = 'yinheqh.ac'
# accnf = 'dongfangqhzjy.ac'

# accnf = 'zrhx.ac'
# accnf = 'htqh.ac'
# accnf = 'htqh.ac'
# accnf = '086038sim24.ac'
# accnf = '116649simstd.ac'
accnf = '116649sim724.ac'


try:
    accinfo = shelve.open(accnf)
    accinfo['BROKER_ID']='9999'
    accinfo['INVESTOR_ID']='116649'
    accinfo['PASSWORD']='ftp123'
    accinfo['ADDR_MD']= "tcp://180.168.146.187:10031"
    accinfo['ADDR_TRADE']= "tcp://180.168.146.187:10030"
    accinfo.close()
    print 'file created.'

except:
    print 'sth wrong'