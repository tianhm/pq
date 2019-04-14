#coding=utf-8 -*-
"This is the main demo file"
from ctp.futures import ApiStruct, MdApi, TraderApi
import time
from copy import deepcopy
import traceback
import threading
from Constant import LOGS_DIR

import colorama
import shelve
import json

# from k_line2 import k_lines, k_lines_list, last_ts_step, process_data
from k_line6 import KLinesPump
# 为每个周期，或每个线程，创建单独的实例
bardict = {}

k_lines_pump60 = KLinesPump()
k_lines_pump120 = KLinesPump()
k_lines_pump180 = KLinesPump()
k_lines_pump300 = KLinesPump()
k_lines_pump600 = KLinesPump()
k_lines_pump780 = KLinesPump()
k_lines_pump900 = KLinesPump()
k_lines_pump1800 = KLinesPump()
k_lines_pump3600 = KLinesPump()



inst = [u'rb1901',u'rb1810',u'hc1901',u'hc1810',u'j1901',u'j1809','AP810','AP901']

ticks=[]
lastprices = []
avprices = []
preclose = []
openprice = []


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


        k_lines_pump60.process_data(depth_market_data=dd, interval=60, save_dir_path='bardata')
        k_lines_pump120.process_data(depth_market_data=dd, interval=120, save_dir_path='bardata')
        k_lines_pump180.process_data(depth_market_data=dd, interval=180, save_dir_path='bardata')
        k_lines_pump300.process_data(depth_market_data=dd, interval=300, save_dir_path='bardata')
        k_lines_pump600.process_data(depth_market_data=dd, interval=600, save_dir_path='bardata')
        k_lines_pump780.process_data(depth_market_data=dd, interval=780, save_dir_path='bardata')
        k_lines_pump900.process_data(depth_market_data=dd, interval=900, save_dir_path='bardata')
        k_lines_pump1800.process_data(depth_market_data=dd, interval=1800, save_dir_path='bardata')
        k_lines_pump3600.process_data(depth_market_data=dd, interval=3600, save_dir_path='bardata')
        


        print dd.LowestPrice, dd.HighestPrice, dd.InstrumentID, dd.UpdateTime
        # print len(ticks), len(lastprices) , len(avprices), len(preclose), len(openprice), len(hhv), len(llv)
        # print 'hhv:', dd.HighestPrice, 'llv:', dd.LowestPrice, 'preclose:', dd.PreClosePrice, 'openprice:', dd.OpenPrice


def mytest(cfgfile = 'zrhx.ac'):

    from ctp_win32 import ApiStruct

    from colorama import init, Fore, Back, Style

    init()

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


    except:
        print  'sth wrong.'
        return


    while True:
        # print len(ticks)
        # print len(k_lines)
        # print k_lines
        # print tick.LastPrice
        # if k_lines_list:
        #     print k_lines_list[-1]

        # print len(k_lines_list)
        # print k_lines_list


        time.sleep(0.1)

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
