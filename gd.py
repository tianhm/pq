#-*- coding:utf-8 -*-
"This is the main demo file"
from ctp.futures import ApiStruct
import time
from copy import deepcopy
import traceback
import threading
import Queue
from TraderDelegate import TraderDelegate, orderList, q_order_list
from Constant import LOGS_DIR

import colorama
import shelve

# traderSpi=TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD)
# traderSpi=TraderDelegate()



msfile='dhqh.ac'
flfile='zrhx.ac'

def followOrder():
    # global orderList
    from ctp_win32 import ApiStruct
    # from Strategy import Strategy

    # s = S = ApiStruct.D_Sell
    # b = B = ApiStruct.D_Buy
    # k = K = ApiStruct.OF_Open
    # p = P = ApiStruct.OF_Close

    # from colorama import init, Fore, Back, Style
    # from TraderDelegate import TraderDelegate
    # from tapy import cross, crossdown

    # init()

    try:

        #读取账户信息
        acinfo = shelve.open(msfile)

        BROKER_ID = acinfo['BROKER_ID']
        INVESTOR_ID = acinfo['INVESTOR_ID']
        PASSWORD = acinfo['PASSWORD']
        ADDR_MD = acinfo['ADDR_MD']
        ADDR_TRADE = acinfo['ADDR_TRADE']
        acinfo.close()

        flacinfo = shelve.open(flfile)

        flBROKER_ID = flacinfo['BROKER_ID']
        flINVESTOR_ID = flacinfo['INVESTOR_ID']
        flPASSWORD = flacinfo['PASSWORD']
        flADDR_MD = flacinfo['ADDR_MD']
        flADDR_TRADE = flacinfo['ADDR_TRADE']
        flacinfo.close()

        master_trade = TraderDelegate(broker_id=BROKER_ID, investor_id=INVESTOR_ID, passwd=PASSWORD, userProductInfo='webstock')
        master_trade.Create(LOGS_DIR + BROKER_ID)

        # T = {}
        # T['TE_RESUME'] = 'int'  # 流重传方式
        # TERT_RESTART = 0  # 从本交易日开始重传
        # TERT_RESUME = 1  # 从上次收到的续传
        # TERT_QUICK = 2  # 只传送登录后的流内容

        master_trade.SubscribePublicTopic(1)
        master_trade.SubscribePrivateTopic(1)

        master_trade.RegisterFront(ADDR_TRADE)
        master_trade.Init()
        print BROKER_ID, INVESTOR_ID
        print u'主帐号登录完成。'


        followTrader1 = TraderDelegate(broker_id=flBROKER_ID, investor_id=flINVESTOR_ID, passwd=flPASSWORD)
        followTrader1.Create('f1')
        followTrader1.RegisterFront(flADDR_TRADE)
        followTrader1.SubscribePublicTopic(ApiStruct.TERT_QUICK)
        followTrader1.SubscribePrivateTopic(ApiStruct.TERT_QUICK)

        followTrader1.Init()

        print u'跟单账号:',flINVESTOR_ID,u'登录完成。'

    except IOError:
        print IOError
        return


    while True:
        try:
            order_master = q_order_list.get(timeout=1)

            q_order_list.task_done()
            om = deepcopy(order_master)
            # order_master = orderList[-1] if orderList else q_order_list.get()
            if om.InvestorID == master_trade.investor_id:
                print u'主帐号下单：'
                print time.asctime(), u'下单时间:', om.InsertTime, u'帐号',om.InvestorID, u'合约:',om.InstrumentID,u'方向:',om.Direction,\
            u'开平:',om.CombOffsetFlag
                print u'数量：',om.VolumeTotalOriginal, u'价格：',om.LimitPrice

            if om.InvestorID == followTrader1.investor_id:
                print u'跟单账号下单：',om
            # print  str(j.FrontID)+str(j.SessionID).strip()+j.OrderRef,j.SequenceNo, j.BrokerOrderSeq, j.RequestID,j.OrderSysID,j.OrderStatus,j.OrderLocalID
            # print j.InsertTime
            # print '--'*50
            # print order_master.InsertDate,
            # print order_master.InsertTime,
            # print order_master.StatusMsg.decode('gbk'),
            # print order_master.OrderSource.decode('gbk')
            # print order_master.BrokerID,
            # print order_master.InvestorID
            # print order_master.InstrumentID,
            # print order_master.LimitPrice,
            # print order_master.Direction,
            # print order_master.CombOffsetFlag
            # print order_master.CombHedgeFlag
            # print order_master.OrderPriceType
            # print order_master.RequestID

            # print order_master.UserProductInfo
            # print order_master.InvestorID, master_trade.investor_id
            if order_master.InvestorID == master_trade.investor_id:

                order = ApiStruct.InputOrder(BrokerID=followTrader1.broker_id, InvestorID=followTrader1.investor_id,UserID=followTrader1.investor_id)
                # order.BrokerID = followTrader1.broker_id
                # order.InvestorID = followTrader1.investor_id
                order.InstrumentID = order_master.InstrumentID
                order.Direction = order_master.Direction
                order.CombHedgeFlag = order_master.CombHedgeFlag
                order.CombOffsetFlag = order_master.CombOffsetFlag
                order.LimitPrice = order_master.LimitPrice
                order.VolumeTotalOriginal = order_master.VolumeTotalOriginal
                order.VolumeTotal = order_master.VolumeTotal
                order.MinVolume = 1
                order.OrderPriceType = order_master.OrderPriceType
                order.OrderRef = order_master.OrderRef
                # order.RequestID = order_master.RequestID
                order.ForceCloseReason = ApiStruct.FCC_NotForceClose
                order.IsAutoSuspend = 1
                order.UserForceClose = 0
                order.TimeCondition = ApiStruct.TC_GFD
                order.VolumeCondition = ApiStruct.VC_AV

                followTrader1.ReqOrderInsert(order,order_master.RequestID)

        except Queue.Empty as e:
            pass

if __name__=="__main__":
    followOrder()