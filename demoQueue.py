#-*- coding=utf-8 -*-
"This is the main demo file"
from ctp.futures import ApiStruct, MdApi, TraderApi
import time
from copy import deepcopy
import traceback
import threading
import queue
from TraderDelegate import TraderDelegate

from Constant import LOGS_DIR

import colorama
import shelve

# import pydevd

#读取账户信息
# cfgfile = 'zrhx.ac'
# acinfo = shelve.open(cfgfile)
# BROKER_ID = acinfo['BROKER_ID']
# INVESTOR_ID = acinfo['INVESTOR_ID']
# PASSWORD = acinfo['PASSWORD']
# ADDR_MD = acinfo['ADDR_MD']
# ADDR_TRADE = acinfo['ADDR_TRADE']
# acinfo.close()

# traderSpi=TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)

# traderSpi=TraderDelegate()

inst = [u'AP810']
inst = [u'rb1810']

q_ticks = queue.Queue()
ticks=[]
lastprices = []
sum = 0

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
        # pydevd.settrace()

    def subscribe_market_data(self, instruments):
        self.SubscribeMarketData(instruments)

    #def OnRspSubMarketData(self, spec_instrument, info, requestid, islast):
    #    print "OnRspSubMarketData"

    #def OnRspUnSubMarketData(self, spec_instrument, info, requestid, islast):
    #    print "OnRspUnSubMarketData"

    def OnRtnDepthMarketData(self, depth_market_data):
        dd = deepcopy(depth_market_data)
        q_ticks.put(dd)

class MyTradeApi(TraderApi):
    def __init__(self, broker_id,
                 investor_id, passwd, *args,**kwargs):
        self.requestid=0
        # self.instruments = instruments
        self.broker_id =broker_id
        self.investor_id = investor_id
        self.passwd = passwd
    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        #print repr(pOrder)
        self.logger.info(u'报单响应,Order=%s' % str(pOrder))
        print pOrder
        if pOrder.OrderStatus == 'a':
            #CTP接受，但未发到交易所
            #print u'CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID))
            self.agent.rtn_order(pOrder)
        else:
            #print u'交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID))
            #self.agent.rtn_order_exchange(pOrder)
            self.agent.rtn_order(pOrder)

    def OnRtnTrade(self, pTrade):
        '''成交通知'''
        self.logger.info(u'TD:成交通知,BrokerID=%s,BrokerOrderSeq = %s,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' %(pTrade.BrokerID,pTrade.BrokerOrderSeq,pTrade.ExchangeID,pTrade.OrderSysID,pTrade.TraderID,pTrade.OrderLocalID))
        self.logger.info(u'TD:成交回报,Trade=%s' % repr(pTrade))
        self.agent.rtn_trade(pTrade)

    def sendOrder(traderSpi, order):
        global mutex
        mutex.acquire()
        print order

        traderSpi.ReqOrderInsert(order, traderSpi.inc_request_id())
        # DatabaseController.insert_SendOrder(order)

        print("sendOrder = " + order.InstrumentID + " dir = " + order.Direction)
        # + " strategy = " + self.__module__)
        time.sleep(1)
        mutex.release()

    def formatOrder(self, inst, direc, open_close, volume, price):
        orderp = ApiStruct.InputOrder(

            InstrumentID=inst,
            Direction=direc,  # ApiStruct.D_Buy or ApiStruct.D_Sell
            OrderRef=str(self.inc_request_id()),
            LimitPrice=price,
            VolumeTotalOriginal=volume,
            OrderPriceType=ApiStruct.OPT_LimitPrice,
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            UserID=self.investor_id,
            CombOffsetFlag=open_close,  # OF_Open, OF_Close, OF_CloseToday
            CombHedgeFlag=ApiStruct.HF_Speculation,
            VolumeCondition=ApiStruct.VC_AV,
            MinVolume=1,
            ForceCloseReason=ApiStruct.FCC_NotForceClose,
            IsAutoSuspend=1,
            UserForceClose=0,
            TimeCondition=ApiStruct.TC_GFD,
        )
        # print orderp
        return orderp

    def PrepareOrder(self, inst, direc, open_close, volume, price):
        order = formatOrder(self, inst, direc, open_close, volume, price)
        print u'send order:', inst, u'price: ', price, u'amount:', volume
        sendOrder(order)


def mytest(cfgfile = 'zrhx.ac'):

    from ctp_win32 import ApiStruct

    from Strategy import Strategy


    s = S = ApiStruct.D_Sell
    b = B = ApiStruct.D_Buy
    k = K = ApiStruct.OF_Open
    p = P = ApiStruct.OF_Close

    from colorama import init, Fore, Back, Style
    init()
    from TraderDelegate import TraderDelegate
    from tapy import cross, crossdown



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

        #登录行情服务器
        user = MyMdApi(instruments=inst, broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
        user.Create("data")
        user.RegisterFront(ADDR_MD)
        user.Init()
        print u'行情服务器登录成功'

        #登录交易服务器
        user_trade = TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
        print BROKER_ID,INVESTOR_ID
        mytrade = MyTradeApi(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
        mytrade.RegisterFront(ADDR_TRADE)
        mytrade.Init()
        mytrade.Join()

        user_trade.Create(LOGS_DIR + "_trader")
        user_trade.RegisterFront(ADDR_TRADE)
        user_trade.Init()
        print u'交易服务器登录成功。'
    except IOError:
        print IOError
        return


    while True:

        tick = q_ticks.get()
        if tick:
            # print tick.LastPrice,tick.UpdateTime, tickn.LastPrice,tickn.UpdateTime, tick.LastPrice - tickn.LastPrice, Fore.YELLOW + str(int(tick.AveragePrice/10))

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
            , Fore.CYAN  + u'振幅:' + str(tick.HighestPrice-tick.LowestPrice), Fore.LIGHTMAGENTA_EX + 'BB: '+str(BB)[:5], 'sig: ',lastsignal
            print Fore.RESET
            # print colorama.Cursor.UP
                

            if tick.LastPrice>tick.AveragePrice:


                # PrepareOrder(traderSpi, tick.InstrumentID, B, K, 1, tick.LastPrice)

                # print Fore.RED+'Buy!!! ' + str(tick.LastPrice - avgprice), tick.InstrumentID
                # print Fore.RESET

                lastsignal = 'bk'

            else:
                lastsignal = 'sk'

                # PrepareOrder(traderSpi, tick.InstrumentID, S, K, 1, tick.LastPrice)

                # print Fore.GREEN + 'Sell!!!  ' + str(tick.LastPrice - avgprice), tick.InstrumentID
                # print Fore.RESET
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
