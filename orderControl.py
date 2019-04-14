#-*- coding:utf-8 -*-

import threading
import time
mutex = threading.Lock()

import sys
if sys.platform == 'win32':
    from ctp_win32 import ApiStruct
elif sys.platform == 'linux2' :
    from ctp_linux64 import ApiStruct


class orderctrl():

    def __init__(self):
        pass


    def sendOrder(self, order):
        global mutex
        mutex.acquire()

        Strategy.traderSpi.ReqOrderInsert(order, Strategy.traderSpi.inc_request_id())
        DatabaseController.insert_SendOrder(order)

        print("sendOrder = " + order.InstrumentID + " dir = " + order.Direction + " strategy = " + self.__module__)
        time.sleep(1)
        mutex.release()


    def formatOrder(self, inst, direc, open_close, volume, price):
        return ApiStruct.InputOrder(
            InstrumentID=inst,
            Direction=direc,  # ApiStruct.D_Buy or ApiStruct.D_Sell
            OrderRef=str(Strategy.traderSpi.inc_request_id()),
            LimitPrice=price,
            VolumeTotalOriginal=volume,
            OrderPriceType=ApiStruct.OPT_LimitPrice,

            BrokerID=Strategy.traderSpi.broker_id,
            InvestorID=Strategy.traderSpi.investor_id,
            CombOffsetFlag=open_close,  # OF_Open, OF_Close, OF_CloseToday
            CombHedgeFlag=ApiStruct.HF_Speculation,

            VolumeCondition=ApiStruct.VC_AV,
            MinVolume=1,
            ForceCloseReason=ApiStruct.FCC_NotForceClose,
            IsAutoSuspend=1,
            UserForceClose=0,
            TimeCondition=ApiStruct.TC_GFD,
        )


    def PrepareOrder(self, inst, direc, open_close, volume, price):
        order = self.formatOrder(inst, direc, open_close, volume, price)
        self.sendOrder(order)
