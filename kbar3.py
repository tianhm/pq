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
from k_line3 import KLinesPump



#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time


__author__ = 'James Iter'
__date__ = '2018/3/27'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


# last_ts_step = 'n'
class KLinesPump(object):

    def __init__(self):
        self.k_lines = dict()
        self.k_lines_list = list()
        self.last_ts_step = 'n'

    def process_data(self, depth_market_data=None, interval=60):
        """
        :param depth_market_data:
        :param interval: 单位(秒)
        :return:
        """
        for key in ['LastPrice', 'TradingDay', 'UpdateTime']:
            if not hasattr(depth_market_data, key):
                return

        date_time = ' '.join([depth_market_data.TradingDay, depth_market_data.UpdateTime])
        ts_step = int(time.mktime(time.strptime(date_time, "%Y%m%d %H:%M:%S"))) / interval
        # global  last_ts_step
        print self.last_ts_step, ts_step

        if self.last_ts_step != ts_step:
            # 此处可以处理一些边界操作。比如对上一个区间的值做特殊处理等。
            print 'I am here. '
            if self.last_ts_step in self.k_lines:
                self.k_lines_list.append(self.k_lines[self.last_ts_step])
                print self.k_lines[self.last_ts_step]
            self.last_ts_step = ts_step

        last_price = depth_market_data.LastPrice

        if ts_step not in self.k_lines:
            self.k_lines[ts_step] = {
                'open': last_price,
                'high': last_price,
                'low': last_price,
                'close': last_price,
                'date_time': date_time
            }

        self.k_lines[ts_step]['close'] = last_price

        if last_price > self.k_lines[ts_step]['high']:
            self.k_lines[ts_step]['high'] = last_price

        elif last_price < self.k_lines[ts_step]['low']:
            self.k_lines[ts_step]['low'] = last_price

        else:
            pass


# 为每个周期，或每个线程，创建单独的实例

k_lines_pump = KLinesPump()
#
# k_lines_pump.process_data(depth_market_data=some_one, interval=some_number)



inst = [u'rb1805']
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

        # k_lines_pump = KLinesPump()
        k_lines_pump.process_data(depth_market_data=dd, interval=60)
                     # \, save_dir_path='bardata')



        # k_lines_pump120 = KLinesPump()     
        # k_lines_pump120.process_data(dd, interval=120, save_dir_path='bardata')
        

        # k_lines_pump180 = KLinesPump()
        # k_lines_pump180.process_data(dd, interval=180, save_dir_path='bardata')
        
        # k_lines_pump300 = KLinesPump()
        # k_lines_pump300.process_data(dd, interval=300, save_dir_path='bardata')
        
        # k_lines_pump600 = KLinesPump()
        # k_lines_pump600.process_data(dd, interval=600, save_dir_path='bardata')
        
        # k_lines_pump780 = KLinesPump()
        # k_lines_pump780.process_data(dd, interval=780, save_dir_path='bardata')
        
        # k_lines_pump900 = KLinesPump()
        # k_lines_pump900.process_data(dd, interval=900, save_dir_path='bardata')
        
        # k_lines_pump1800 = KLinesPump()
        # k_lines_pump1800.process_data(dd, interval=1800, save_dir_path='bardata')
        
        # k_lines_pump3600 = KLinesPump()
        # k_lines_pump3600.process_data(dd, interval=3600, save_dir_path='bardata')






        # process_data(dd,interval=60)
        # process_data(dd,interval=120)
        # process_data(dd,interval=180)
        # process_data(dd,interval=300)
        # process_data(dd,interval=600)
        # process_data(dd,interval=780)
        # process_data(dd,interval=900)
        # process_data(dd,interval=1800)
        # process_data(dd,interval=3600)
        
        print dd.LowestPrice, dd.HighestPrice, dd.InstrumentID, dd.UpdateTime
        # print len(ticks), len(lastprices) , len(avprices), len(preclose), len(openprice), len(hhv), len(llv)
        # print 'hhv:', dd.HighestPrice, 'llv:', dd.LowestPrice, 'preclose:', dd.PreClosePrice, 'openprice:', dd.OpenPrice

        # print depth_market_data.BidPrice1,depth_market_data.BidVolume1,depth_market_data.AskPrice1,depth_market_data.AskVolume1,depth_market_data.LastPrice,depth_market_data.Volume,depth_market_data.UpdateTime,depth_market_data.UpdateMillisec,depth_market_data.InstrumentID

#inst=[u'al1008', u'al1009', u'al1010', u'al1011', u'al1012', u'al1101', u'al1102', u'al1103', u'al1104', u'al1105', u'al1106', u'al1107', u'au1008', u'au1009', u'au1010', u'au1011', u'au1012', u'au1101', u'au1102', u'au1103', u'au1104', u'au1105', u'au1106', u'au1107', u'cu1008', u'cu1009', u'cu1010', u'cu1011', u'cu1012', u'cu1101', u'cu1102', u'cu1103', u'cu1104', u'cu1105', u'cu1106', u'cu1107', u'fu1009', u'fu1010', u'fu1011', u'fu1012', u'fu1101', u'fu1103', u'fu1104', u'fu1105', u'fu1106', u'fu1107', u'fu1108', u'rb1008', u'rb1009', u'rb1010', u'rb1011', u'rb1012', u'rb1101', u'rb1102', u'rb1103', u'rb1104', u'rb1105', u'rb1106', u'rb1107', u'ru1008', u'ru1009', u'ru1010', u'ru1011', u'ru1101', u'ru1103', u'ru1104', u'ru1105', u'ru1106', u'ru1107', u'wr1008', u'wr1009', u'wr1010', u'wr1011', u'wr1012', u'wr1101', u'wr1102', u'wr1103', u'wr1104', u'wr1105', u'wr1106', u'wr1107', u'zn1008', u'zn1009', u'zn1010', u'zn1011', u'zn1012', u'zn1101', u'zn1102', u'zn1103', u'zn1104', u'zn1105', u'zn1106']


def mytest(cfgfile = '086038simstd.ac'):

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
