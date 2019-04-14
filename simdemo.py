#-*- coding=utf-8 -*-
"This is the main demo file"
from ctp.futures import ApiStruct, MdApi, TraderApi
import time
from copy import deepcopy
import traceback
import threading
from TraderDelegate import TraderDelegate

from Constant import LOGS_DIR

import colorama
# import shelve

# #读取账户信息
# cfgfile = 'zrhx.ac'
# acinfo = shelve.open(cfgfile)
# BROKER_ID = acinfo['BROKER_ID']
# INVESTOR_ID = acinfo['INVESTOR_ID']
# PASSWORD = acinfo['PASSWORD']
# ADDR_MD = acinfo['ADDR_MD']
# ADDR_TRADE = acinfo['ADDR_TRADE']
# acinfo.close()

# traderSpi=TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)




traderSpi=TraderDelegate()

inst = [u'rb1805']
ticks=[]
lastprices = []
avprices = []
singnals = []

mutex = threading.Lock()

class MyMdApi(MdApi):
    def __init__(self, instruments, broker_id,
                 investor_id, passwd, *args,**kwargs):
        self.requestid=0
        self.instruments = instruments
        self.broker_id =broker_id
        self.investor_id = investor_id
        self.passwd = passwd

    def OnRspError(self, info, RequestId, IsLast):
        print " Error"
        self.isErrorRspInfo(info)

    def isErrorRspInfo(self, info):
        if info.ErrorID !=0:
            print "ErrorID=", info.ErrorID, ", ErrorMsg=", info.ErrorMsg
        return info.ErrorID !=0

    def OnFrontDisConnected(self, reason):
        print "onFrontDisConnected:", reason

    def OnHeartBeatWarning(self, time):
        print "onHeartBeatWarning", time

    def OnFrontConnected(self):
        print "OnFrontConnected:"
        self.user_login(self.broker_id, self.investor_id, self.passwd)

    def user_login(self, broker_id, investor_id, passwd):
        req = ApiStruct.ReqUserLogin(BrokerID=broker_id, UserID=investor_id, Password=passwd)

        self.requestid+=1
        r=self.ReqUserLogin(req, self.requestid)

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        print "OnRspUserLogin", is_last, info
        if is_last and not self.isErrorRspInfo(info):
            print "get today's trading day:", repr(self.GetTradingDay())
            self.subscribe_market_data(self.instruments)

    def subscribe_market_data(self, instruments):
        self.SubscribeMarketData(instruments)

    #def OnRspSubMarketData(self, spec_instrument, info, requestid, islast):
    #    print "OnRspSubMarketData"

    #def OnRspUnSubMarketData(self, spec_instrument, info, requestid, islast):
    #    print "OnRspUnSubMarketData"

    def OnRtnDepthMarketData(self, depth_market_data):
        # print depth_market_data
        # print 'orig time',depth_market_data.UpdateTime
        dd = deepcopy(depth_market_data)
        ticks.append(dd)
        lastprices.append(dd.LastPrice)
        avprices.append(int(dd.AveragePrice/10))

        print len(ticks), len(lastprices) , len(avprices)

        # print depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec,depth_market_data.InstrumentID

#inst=[u'al1008', u'al1009', u'al1010', u'al1011', u'al1012', u'al1101', u'al1102', u'al1103', u'al1104', u'al1105', u'al1106', u'al1107', u'au1008', u'au1009', u'au1010', u'au1011', u'au1012', u'au1101', u'au1102', u'au1103', u'au1104', u'au1105', u'au1106', u'au1107', u'cu1008', u'cu1009', u'cu1010', u'cu1011', u'cu1012', u'cu1101', u'cu1102', u'cu1103', u'cu1104', u'cu1105', u'cu1106', u'cu1107', u'fu1009', u'fu1010', u'fu1011', u'fu1012', u'fu1101', u'fu1103', u'fu1104', u'fu1105', u'fu1106', u'fu1107', u'fu1108', u'rb1008', u'rb1009', u'rb1010', u'rb1011', u'rb1012', u'rb1101', u'rb1102', u'rb1103', u'rb1104', u'rb1105', u'rb1106', u'rb1107', u'ru1008', u'ru1009', u'ru1010', u'ru1011', u'ru1101', u'ru1103', u'ru1104', u'ru1105', u'ru1106', u'ru1107', u'wr1008', u'wr1009', u'wr1010', u'wr1011', u'wr1012', u'wr1101', u'wr1102', u'wr1103', u'wr1104', u'wr1105', u'wr1106', u'wr1107', u'zn1008', u'zn1009', u'zn1010', u'zn1011', u'zn1012', u'zn1101', u'zn1102', u'zn1103', u'zn1104', u'zn1105', u'zn1106']

def sendOrder(order):
    global mutex
    mutex.acquire()
    print order

    traderSpi.ReqOrderInsert(order, traderSpi.inc_request_id())
    # DatabaseController.insert_SendOrder(order)

    print("sendOrder = " + order.InstrumentID + " dir = " + order.Direction)
     # + " strategy = " + self.__module__)
    time.sleep(1)
    mutex.release()




def formatOrder(traderSpi, inst, direc, open_close, volume, price):
    orderp = ApiStruct.InputOrder(
        InstrumentID=inst,
        Direction=direc, # ApiStruct.D_Buy or ApiStruct.D_Sell
        OrderRef=str(traderSpi.inc_request_id()),
        LimitPrice=price,
        VolumeTotalOriginal=volume,
        OrderPriceType=ApiStruct.OPT_LimitPrice,

        BrokerID=traderSpi.broker_id,
        InvestorID=traderSpi.investor_id,
        UserID = traderSpi.investor_id,
        CombOffsetFlag=open_close, # OF_Open, OF_Close, OF_CloseToday
        CombHedgeFlag=ApiStruct.HF_Speculation,

        VolumeCondition=ApiStruct.VC_AV,
        MinVolume=1,
        ForceCloseReason=ApiStruct.FCC_NotForceClose,
        IsAutoSuspend=1,
        UserForceClose=0,
        TimeCondition=ApiStruct.TC_GFD,
    )
    print orderp
    return orderp 


def PrepareOrder(traderSpi, inst, direc, open_close, volume, price):
    order = formatOrder(traderSpi,inst, direc, open_close, volume, price)
    print u'发单', inst, u'price：', price, u'amount:', volume
    sendOrder(order)



    # ,u'hc1805',u'hc1810']


def mytest(cfgfile = '086038simstd.ac'):

    from ctp_win32 import ApiStruct

    from Strategy import Strategy


    s = S = ApiStruct.D_Sell
    b = B = ApiStruct.D_Buy
    k = K = ApiStruct.OF_Open
    p = P = ApiStruct.OF_Close

    from colorama import init, Fore, Back, Style

    from TraderDelegate import TraderDelegate

    from tapy import cross, crossdown


    init()

    lastsignal = 'nosig'

    print cfgfile
    try:

        import shelve

        #读取账户信息
        acinfo = shelve.open(cfgfile)
        BROKER_ID = acinfo['BROKER_ID']
        INVESTOR_ID = acinfo['INVESTOR_ID']
        PASSWORD = acinfo['PASSWORD']
        ADDR_MD = acinfo['ADDR_MD']
        ADDR_TRADE = acinfo['ADDR_TRADE']
        acinfo.close()

        traderSpi=TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)

        #登录行情服务器
        user = MyMdApi(instruments=inst, broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
        user.Create("data")
        user.RegisterFront(ADDR_MD)
        user.Init()
        print u'行情服务器登录成功'

        #登录交易服务器
        user_trade = TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
        print BROKER_ID,INVESTOR_ID

        user_trade.Create(LOGS_DIR + "_trader")
        user_trade.RegisterFront(ADDR_TRADE)
        user_trade.Init()
        print u'交易服务器登录成功。'
    except:
        print  'sth wrong.'


    while True:
        # print len(ticks)

        if len(ticks)>10 and len(lastprices) > 10:

            ticks1=ticks[-10:]

            lastprices.pop(0)

            # print len(ticks1)
            # for l in ticks:
            # 	print l.UpdateTime


            tick = ticks1[-1]
            tickn = ticks1[0]

            # print tick.LastPrice,tick.UpdateTime, tickn.LastPrice,tickn.UpdateTime, tick.LastPrice - tickn.LastPrice, Fore.YELLOW + str(int(tick.AveragePrice/10))

            if tick.LastPrice != tickn.LastPrice:

                avgprice = int(tick.AveragePrice/10)
                HH =  tick.HighestPrice
                LL = tick.LowestPrice
                OO = tick.OpenPrice
                CC = tick.LastPrice
                if HH - LL >0 :
                    BB = (CC - LL) / (HH - LL)
                else:
                    BB = 0.5

                print time.strftime('%m%d %H:%M:%S'), Fore.WHITE + INVESTOR_ID, Fore.GREEN+tick.InstrumentID, Fore.WHITE + Style.BRIGHT+ u'现价:' + str(tick.LastPrice ), Fore.YELLOW + u'均价:'+str(avgprice)\
                , Fore.CYAN  + u'振幅:' + str(tick.HighestPrice-tick.LowestPrice), Fore.LIGHTMAGENTA_EX + 'BB: '+str(BB)[:5]
                print Fore.RESET
                # print colorama.Cursor.UP

                print lastsignal

                

                if cross(lastprices,avgprice -4) and lastsignal != 'bk':              # ?if tick.LastPrice - avgprice > 3:


                    PrepareOrder(traderSpi, tick.InstrumentID, B, K, 1, tick.LastPrice)

                    print Fore.RED+'Buy!!! ' + str(tick.LastPrice - avgprice), tick.InstrumentID
                    print Fore.RESET

                    lastsignal = 'bk'

                elif crossdown(lastprices, avgprice + 4) and lastsignal != 'sk':

                    PrepareOrder(traderSpi, tick.InstrumentID, S, K, 1, tick.LastPrice)

                    print Fore.GREEN + 'Sell!!!  ' + str(tick.LastPrice - avgprice), tick.InstrumentID
                    print Fore.RESET
                    lastsignal = 'sk'

        time.sleep(1)

if __name__=="__main__":
    import sys
    print sys.argv
    if len(sys.argv)>1:
        # break
        cfgfile = sys.argv[1]
        print cfgfile
        mytest(cfgfile)
    else:
        mytest()
