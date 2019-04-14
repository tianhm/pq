#-*- coding:utf-8 -*-
from FinalLogger import logger
from DatabaseController import DatabaseController
import logging
import sys
from agent import AbsAgent, Agent
import bisect
import Queue
orderList = []
q_order_list = Queue.Queue()
import pydevd

if sys.platform == 'win32':
    from ctp_win32 import ApiStruct, TraderApi
elif sys.platform == 'linux2' :
    from ctp_linux64 import ApiStruct, TraderApi




class agent(Agent):

    def __init__(self):
        ##命令队列(不区分查询和交易)
        self.commands = []  #每个元素为(trigger_tick,func), 用于当tick==trigger_tick时触发func
        self.tick = 0


    def get_tick(self):
        return self.tick

    def put_command(self,trigger_tick,command): #按顺序插入
        #print func_name(command)
        cticks = [ttick for ttick,cmd in self.commands] #不要用command这个名称，否则会覆盖传入的参数,导致后面的插入操作始终插入的是原序列最后一个command的拷贝
        ii = bisect.bisect(cticks,trigger_tick)
        #print 'trigger_tick=%s,cticks=%s,len(command)=%s' % (trigger_tick,str(cticks),len(self.commands))
        self.commands.insert(ii,(trigger_tick,command))
        logging.debug(u'AA_P:trigger_tick=%s,cticks=%s,len(command)=%s' % (trigger_tick,str(cticks),len(self.commands)))


    def rtn_order(self,sorder):
        '''
            交易所接受下单回报(CTP接受的已经被过滤)
            暂时只处理撤单的回报.
        '''
        import copy
        # global orderList
        # print 'rtn_order ing....'
        # print sorder
        # print(type(sorder))
        # print sorder.InsertTime
        # print sorder.InvestorID
        # print sorder.StatusMsg.decode('gbk')

        orderList.append(copy.deepcopy(sorder))
        q_order_list.put(copy.deepcopy(sorder))
        # print orderList

        logging.info(u'成交/撤单回报:%s' % (str(sorder,)))
        if sorder.OrderStatus == ApiStruct.OST_Canceled or sorder.OrderStatus == ApiStruct.OST_PartTradedNotQueueing:   #完整撤单或部成部撤
            logging.info(u'撤单, 撤销开/平仓单')
            ##查询可用资金
            self.put_command(self.get_tick()+1,self.fetch_trading_account)
            ##处理相关Order

            # myorder = self.ref2order[int(sorder.OrderRef)]
            # if myorder.action_type == XOPEN:    #开仓指令cancel时需要处理，平仓指令cancel时不需要处理
            #     logging.info(u'撤销开仓单')
            #     myorder.on_cancel()



class TraderDelegate(TraderApi):

    logger = logging.getLogger('ctp.MdSpiDelegate')
    def __init__(self, broker_id='', investor_id='', passwd='', *args,**kwargs):
        self.requestid=0
        self.broker_id =broker_id
        self.investor_id = investor_id
        self.passwd = passwd

        self.agent = agent()

    def OnRspError(self, info, RequestId, IsLast):
        self.isErrorRspInfo(info)

    def isErrorRspInfo(self, info):
        if info.ErrorID !=0:
            logger.info('ErrorID=%d, ErrorMsg=%s' % (info.ErrorID, info.ErrorMsg.decode('gbk')))
        return info.ErrorID !=0

    def OnFrontDisConnected(self, reason):
        logger.info('onFrontDisConnected, reason = %d' % reason)

    def OnHeartBeatWarning(self, time):
        logger.info('OnHeartBeatWarning, time = %s' % time)

    def OnFrontConnected(self):
        logger.info('OnFrontConnected')
        req = ApiStruct.ReqUserLogin(BrokerID=self.broker_id, UserID=self.investor_id, Password=self.passwd)
        self.ReqUserLogin(req, self.inc_request_id())

    def OnRspUserLogin(self, userlogin, info, rid, is_last):
        if is_last and not self.isErrorRspInfo(info):
            logger.info('OnRspUserLogin %s' % is_last)
            req = ApiStruct.SettlementInfoConfirm(BrokerID=self.broker_id, InvestorID=self.investor_id)
            self.ReqSettlementInfoConfirm(req, self.inc_request_id())

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        print u'报单回报。',pInputOrder
        if bIsLast and not self.isErrorRspInfo(pRspInfo):
            print u'报单回报：',pInputOrder
            logger.info('OnRspOrderInsert %s' % pInputOrder.InstrumentID)

    def inc_request_id(self):
        self.requestid += 1
        return self.requestid

    def OnRtnOrder(self, pOrder):
        ''' 报单通知
            CTP、交易所接受报单
            Agent中不区分，所得信息只用于撤单
        '''
        #print repr(pOrder)
        # self.logger.info(u'报单响应,Order=%s' % str(pOrder))
        # print '................'
        # self.agent.rtn_order(pOrder)


        if pOrder.OrderStatus == 'a':
            print u'CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID)
            # self.logger.info(u'TD:CTP接受Order，但未发到交易所, BrokerID=%s,BrokerOrderSeq = %s,TraderID=%s, OrderLocalID=%s' % (pOrder.BrokerID,pOrder.BrokerOrderSeq,pOrder.TraderID,pOrder.OrderLocalID))
            # self.agent.rtn_order(pOrder)
        else:
            print u'交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID)
            self.logger.info(u'TD:交易所接受Order,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' % (pOrder.ExchangeID,pOrder.OrderSysID,pOrder.TraderID,pOrder.OrderLocalID))
            #self.agent.rtn_order_exchange(pOrder)
            self.agent.rtn_order(pOrder)
            # orderList.append(pOrder)
            # print 'thm test sig.'

    def OnRtnTrade(self, pTrade):
        '''成交通知'''
        # print pTrade
        self.logger.info(u'TD:成交通知,BrokerID=%s,BrokerOrderSeq = %s,exchangeID=%s,OrderSysID=%s,TraderID=%s, OrderLocalID=%s' %(pTrade.BrokerID,pTrade.BrokerOrderSeq,pTrade.ExchangeID,pTrade.OrderSysID,pTrade.TraderID,pTrade.OrderLocalID))
        self.logger.info(u'TD:成交回报,Trade=%s' % repr(pTrade))
        # self.agent.rtn_trade(pTrade)

    def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
        '''
            ctp撤单校验错误
        '''
        self.logger.warning(u'TD:CTP撤单录入错误回报, 正常后不应该出现,rspInfo=%s'%(str(pRspInfo),))
        #self.agent.rsp_order_action(pInputOrderAction.OrderRef,pInputOrderAction.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)
        self.agent.err_order_action(pInputOrderAction.OrderRef,pInputOrderAction.InstrumentID,pRspInfo.ErrorID,pRspInfo.ErrorMsg)



if __name__=="__main__":
    pass

