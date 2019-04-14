# encoding: UTF-8

'''
本文件包含了CTA引擎中策略开发用模板(目前支持双合约)
'''
import datetime
import ctaEngine
import requests
import copy
import os
import json
import talib
import numpy as np
from collections import OrderedDict
from ctaBase import *
from vtConstant import *
from vtObject import *
from threading import Thread
from PyQt4.QtCore import Qt, QTimer
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QApplication


########################################################################
class CtaTemplate():
    """CTA策略模板"""

    # 策略类的名称和作者
    author = EMPTY_UNICODE
    className = 'CtaTemplate'

    # MongoDB数据库的名称，K线数据库默认为1分钟
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME

    t = None
    qtsp = None

    # 策略的基本参数
    name = EMPTY_UNICODE  # 策略实例名称
    vtSymbol = EMPTY_STRING  # 交易的合约vt系统代码
    symbolList = []  # 所有需要订阅的合约
    exchangeList = []  # 所有需要订阅合约的交易所
    crossSize = {}  # 盘口撮合量

    # 无限易客户端相关变量
    exchange = EMPTY_STRING  # 交易的合约vt系统代码
    paramMap = {}  # 参数显示映射表
    varMap = {}  # 变量显示映射表

    # 策略的基本变量，由引擎管理
    inited = False  # 是否进行了初始化
    trading = False  # 是否启动交易，由引擎管理
    backtesting = False  # 回测模式

    # 策略内部管理的仓位
    pos = {}  # 总投机方向
    tpos0L = {}  # 今持多仓
    tpos0S = {}  # 今持空仓
    ypos0L = {}  # 昨持多仓
    ypos0S = {}  # 昨持空仓

    # 参数列表，保存了参数的名称，去除'symbolList',当前版本不支持多合约
    baseparamList = ['name',
                     'author',
                     'className',
                     'vtSymbol',
                     'exchange']

    # 变量列表，保存了变量的名称
    basevarList = ['inited',
                   'trading',
                   'pos']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine

        # 无限易客户端需要
        self.sid = 0  # 策略ID
        self.vtSymbol = EMPTY_STRING  # 合约
        self.exchange = EMPTY_STRING  # 交易的合约vt系统代码
        # 策略的基本变量，由引擎管理
        self.inited = False  # 是否进行了初始化
        self.trading = False  # 是否启动交易，由引擎管理
        self.backtesting = False  # 回测模式

        self.bar = None  # K线对象
        self.barMinute = EMPTY_INT  # K线当前的分钟

        self.orderID = None  # 上一笔订单
        self.tradeDate = None  # 当前交易日

        # 仓位信息
        self.pos = {}  # 总投机方向
        self.tpos0L = {}  # 今持多仓
        self.tpos0S = {}  # 今持空仓
        self.ypos0L = {}  # 昨持多仓
        self.ypos0S = {}  # 昨持空仓

        # 定义尾盘，判断是否要进行交易
        self.endOfDay = False
        self.buySig = False
        self.shortSig = False
        self.coverSig = False
        self.sellSig = False

        # 默认交易价格
        self.longPrice = EMPTY_FLOAT  # 多头开仓价
        self.shortPrice = EMPTY_FLOAT  # 空头开仓价

        # 默认技术指标列表
        self.am = ArrayManager(size=100)

        # 回测需要
        self.crossSize = {}  # 盘口撮合量

        # 参数和状态
        self.varList = self.basevarList + self.varList
        self.paramList = self.baseparamList + self.paramList

        # 设置策略的参数
        self.onUpdate(setting)

        # 用于界面显示的映射表
        if not self.paramMap:
            self.paramMap = dict(zip(self.paramList, self.paramList))
        if not self.varMap:
            self.varMap = dict(zip(self.varList, self.varList))
        self.paramMapReverse = {v: k for k, v in self.paramMap.items()}
        self.varMapReverse = {v: k for k, v in self.varMap.items()}

        self.widget = None
        self.paramLoaded = False

    # ----------------------------------------------------------------------
    def onUpdate(self, setting):
        """刷新策略"""
        # 按输入字典更新
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]

        self.vtSymbol = str(self.vtSymbol)
        self.exchange = str(self.exchange)

        # 所有需要订阅的合约
        self.symbolList = self.vtSymbol.split(';')
        self.exchangeList = self.exchange.split(';')

        # 初始化仓位信息
        self.pos = {}  # 总投机方向
        self.tpos0L = {}  # 今持多仓
        self.tpos0S = {}  # 今持空仓
        self.ypos0L = {}  # 昨持多仓
        self.ypos0S = {}  # 昨持空仓
        for symbol in self.symbolList:
            self.pos[symbol] = 0
            self.ypos0L[symbol] = 0
            self.tpos0L[symbol] = 0
            self.ypos0S[symbol] = 0
            self.tpos0S[symbol] = 0

    @classmethod
    # ----------------------------------------------------------------------
    def setQtSp(cls):
        """重新订阅合约"""
        if cls.t is None:
            cls.t = Thread(target=cls.StartGui)
            cls.t.setDaemon(True)
            cls.t.start()

    # ----------------------------------------------------------------------
    def subSymbol(self):
        """重新订阅合约"""
        for symbol, exchange in zip(self.symbolList, self.exchangeList):
            ctaEngine.subMarketData( \
                {'sid': self, \
                 'InstrumentID': str(symbol), \
                 'ExchangeID': str(exchange)})

    # ----------------------------------------------------------------------
    def unSubSymbol(self):
        """重新订阅合约"""
        for symbol, exchange in zip(self.symbolList, self.exchangeList):
            ctaEngine.unsubMarketData( \
                {'sid': self, \
                 'InstrumentID': str(symbol), \
                 'ExchangeID': str(exchange)})

    # ----------------------------------------------------------------------
    def setParam(self, setting):
        """刷新参数"""
        updateSymbol = False
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in self.paramMap and self.paramMap[key].encode('gbk') in setting:
                    # 修改合约参数就重新订阅
                    if key == 'vtSymbol':
                        d[key] = setting[self.paramMap[key].encode('gbk')]
                    elif key == 'exchange':
                        d[key] = setting[self.paramMap[key].encode('gbk')]
                    else:
                        try:
                            d[key] = eval(setting[self.paramMap[key].encode('gbk')])
                        except:
                            d[key] = setting[self.paramMap[key].encode('gbk')]

        # 初始化仓位信息
        self.symbolList = d['vtSymbol'].split(';')
        self.exchangeList = d['exchange'].split(';')
        self.pos = {}
        self.tpos0L = {}
        self.tpos0S = {}
        self.ypos0L = {}
        self.ypos0S = {}
        for symbol in self.symbolList:
            self.pos[symbol] = 0
            self.ypos0L[symbol] = 0
            self.tpos0L[symbol] = 0
            self.ypos0S[symbol] = 0
            self.tpos0S[symbol] = 0

        param = {"sid": self.sid}
        param.update(setting)
        ctaEngine.updateParam(param)
        self.putEvent()

    # ----------------------------------------------------------------------
    def getParam(self):
        """获取参数"""
        setting = OrderedDict()
        for key in reversed(self.paramList):
            if key in self.paramMap:
                setting[self.paramMap[key]] = str(getattr(self, key))
        return setting

    # ----------------------------------------------------------------------
    def getParamOrgin(self):
        """获取参数"""
        setting = {}
        for key in reversed(self.paramList):
            setting[key] = getattr(self, key)
        return setting

    # ----------------------------------------------------------------------
    def getVar(self):
        """获取变量"""
        setting = OrderedDict()
        d = self.__dict__
        for key in self.varList:
            setting[key] = str(d[key])
        return setting

        # ----------------------------------------------------------------------

def onInit(self):
    """初始化策略（必须由用户继承实现）"""
    try:
        if not self.paramLoaded:
            self.paramLoaded = True
            path = os.path.split(os.path.realpath(__file__))[0] + '\\json\\'
            with open(path + self.name + '.josn') as f:
                setting = json.loads(f.read())
                self.onUpdate(setting)
            self.output(u'使用保存参数')
    except:
        pass
    self.setQtSp()
    self.output(u'%s策略初始化' % self.name)
    self.inited = True
    self.putEvent()


    # ----------------------------------------------------------------------


def onStart(self):
    """启动策略（必须由用户继承实现）"""
    self.trading = True
    self.subSymbol()
    self.output(u'%s策略启动' % self.name)
    self.putEvent()
    if (not self.widget is None) and (not self.bar is None):
        self.widget.signalLoad.emit()


        # ----------------------------------------------------------------------


def onStop(self):
    """停止策略（必须由用户继承实现）"""
    self.unSubSymbol()
    self.output(u'%s策略停止' % self.name)
    setting = self.getParamOrgin()
    try:
        path = os.path.split(os.path.realpath(__file__))[0] + '\\json\\'
        with open(path + self.name + '.josn', 'w') as f:
            f.write(json.dumps(setting))
        self.output(u'保存策略参数')
    except:
        self.output(traceback.format_exc())
    if not self.widget is None:
        self.widget.clear()
    self.trading = False
    self.putEvent()


    # ----------------------------------------------------------------------


def onTick(self, tick):
    """收到行情TICK推送（必须由用户继承实现）"""
    # 判断交易日更新
    if self.tradeDate is None:
        self.tradeDate = tick.date
    elif not self.tradeDate == tick.date:
        self.output(u'当前交易日 ：' + tick.date)
        self.tradeDate = tick.date
        for symbol in self.symbolList:
            self.ypos0L[symbol] += self.tpos0L[symbol]
            self.tpos0L[symbol] = 0
            self.ypos0S[symbol] += self.tpos0S[symbol]
            self.tpos0S[symbol] = 0


# ----------------------------------------------------------------------
def onOrderCancel(self, order):
    """收到委托变化推送（必须由用户继承实现）"""
    self.orderID = None


# ----------------------------------------------------------------------
def onOrderTrade(self, order):
    """收到委托变化推送（必须由用户继承实现）"""
    self.orderID = None

    # ----------------------------------------------------------------------


def onOrder(self, order, log=False):
    """收到委托变化推送（必须由用户继承实现）"""
    if order is None:
        return
    # 对于无需做细粒度委托控制的策略，可以忽略onOrder
    # CTA委托  类型映射
    offset = order.offset
    status = order.status
    if status == u'已撤销':
        self.onOrderCancel(order)
    elif status == u'全部成交' or status == u'部成部撤':
        self.onOrderTrade(order)
    if log:
        self.output(' '.join([offset, status]))
        self.output('')


# ----------------------------------------------------------------------
def onErr(self, error):
    """收到错误推送（必须由用户继承实现）"""
    if 'errCode' in error:
        errCode = error['errCode']
    if 'errMsg' in error:
        errMsg = error['errMsg']
        self.writeCtaLog(errMsg)

        # ----------------------------------------------------------------------


def onTrade(self, trade, log=False):
    """收到成交推送（必须由用户继承实现）"""
    if trade is None:
        return
    price = trade.price
    volume = trade.volume
    symbol = trade.vtSymbol
    offset = trade.offset
    direction = trade.direction
    if direction == u'多':
        self.pos[symbol] += volume
        if offset == u'开仓':
            self.tpos0L[symbol] += volume
        elif offset == u'平今':
            self.tpos0S[symbol] -= volume
        elif offset == u'平仓' or offset == u'平昨':
            self.ypos0S[symbol] -= volume
    elif direction == u'空':
        self.pos[symbol] -= volume
        if offset == u'开仓':
            self.tpos0S[symbol] += volume
        elif offset == u'平仓' or offset == u'平昨':
            self.ypos0L[symbol] -= volume
        elif offset == u'平今':
            self.tpos0L[symbol] -= volume
    if log:
        self.output(trade.tradeTime
                    + u' 合约|' + str(symbol)
                    + u'|{}{}成交|'.format(direction, offset) + str(price)
                    + u'|手数|' + str(volume))
    self.output(u' ')


    # ----------------------------------------------------------------------


def onBar(self, bar):
    """收到Bar推送（必须由用户继承实现）"""
    self.bar = bar
    if self.tradeDate != bar.date:
        self.tradeDate = bar.date

    # 记录数据
    if not self.am.updateBar(bar):
        return

    # 计算指标
    self.getCtaIndictor(bar)

    # 计算信号
    self.getCtaSignal(bar)

    # 简易信号执行
    self.execSignal(self.V)

    # 发出状态更新事件
    self.putEvent()


# ----------------------------------------------------------------------
def onXminBar(self, bar):
    """收到Bar推送（必须由用户继承实现）"""
    self.bar = bar
    if self.tradeDate != bar.date:
        self.tradeDate = bar.date

    # 记录数据
    if not self.am.updateBar(bar):
        return

    # 计算指标
    self.getCtaIndictor(bar)

    # 计算信号
    self.getCtaSignal(bar)

    # 简易信号执行
    self.execSignal(self.V)

    # 发出状态更新事件
    self.putEvent()


# ----------------------------------------------------------------------
def execSignal(self, volume):
    """简易交易信号执行"""
    pos = self.pos[self.vtSymbol]
    endOfDay = self.endOfDay
    # 挂单未成交
    if not self.orderID is None:
        self.cancelOrder(self.orderID)

    # 当前无仓位
    if pos == 0 and not self.endOfDay:
        # 买开，卖开
        if self.shortSig:
            self.orderID = self.short(self.shortPrice, volume)
        elif self.buySig:
            self.orderID = self.buy(self.longPrice, volume)

    # 持有多头仓位
    elif pos > 0 and (self.sellSig or self.endOfDay):
        self.orderID = self.sell(self.shortPrice, pos)

    # 持有空头仓位
    elif pos < 0 and (self.coverSig or self.endOfDay):
        self.orderID = self.cover(self.longPrice, -pos)

        # ----------------------------------------------------------------------


def sell_y(self, price, volume, symbol='', exchange='', stop=False):
    """卖平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_SELL, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def sell_t(self, price, volume, symbol='', exchange='', stop=False):
    """卖平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def buy(self, price, volume, symbol='', exchange='', stop=False):
    """买开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_BUY, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def short(self, price, volume, symbol='', exchange='', stop=False):
    """卖开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_SHORT, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def sell(self, price, volume, symbol='', exchange='', stop=False):
    """卖平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0L = self.tpos0L.get(symbol)
    ypos0L = self.ypos0L.get(symbol)
    if tpos0L >= volume:
        return self.sendOrder(CTAORDER_SELL_TODAY, price, volume, symbol, exchange)
    elif ypos0L >= volume:
        return self.sendOrder(CTAORDER_SELL, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------


def cover(self, price, volume, symbol='', exchange='', stop=False):
    """买平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0S = self.tpos0S.get(symbol)
    ypos0S = self.ypos0S.get(symbol)
    if tpos0S >= volume:
        return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, exchange)
    elif ypos0S >= volume:
        return self.sendOrder(CTAORDER_COVER, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------


def cover_y(self, price, volume, symbol='', exchange='', stop=False):
    """买平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_COVER, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def cover_t(self, price, volume, symbol='', exchange='', stop=False):
    """买平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrder(CTAORDER_COVER_TODAY, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def buy_fok(self, price, volume, symbol='', exchange='', stop=False):
    """买开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrderFOK(CTAORDER_BUY, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def sell_fok(self, price, volume, symbol='', exchange='', stop=False):
    """卖平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0L = self.tpos0L.get(symbol)
    ypos0L = self.ypos0L.get(symbol)
    if tpos0L >= volume:
        return self.sendOrderFOK(CTAORDER_SELL_TODAY, price, volume, symbol, exchange)
    elif ypos0L >= volume:
        return self.sendOrderFOK(CTAORDER_SELL, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------


def short_fok(self, price, volume, symbol='', exchange='', stop=False):
    """卖开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrderFOK(CTAORDER_SHORT, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------





def cover_fok(self, price, volume, symbol='', exchange='', stop=False):
    """买平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0S = self.tpos0S.get(symbol)
    ypos0S = self.ypos0S.get(symbol)
    if tpos0S >= volume:
        return self.sendOrderFOK(CTAORDER_COVER_TODAY, price, volume, symbol, exchange)
    elif ypos0S >= volume:
        return self.sendOrderFOK(CTAORDER_COVER, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------


def buy_fak(self, price, volume, symbol='', exchange='', stop=False):
    """买开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrderFAK(CTAORDER_BUY, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------



def sell_fak(self, price, volume, symbol='', exchange='', stop=False):
    """卖平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0L = self.tpos0L.get(symbol)
    ypos0L = self.ypos0L.get(symbol)
    if tpos0L >= volume:
        return self.sendOrderFAK(CTAORDER_SELL_TODAY, price, volume, symbol, exchange)
    elif ypos0L >= volume:
        return self.sendOrderFAK(CTAORDER_SELL, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------



def short_fak(self, price, volume, symbol='', exchange='', stop=False):
    """卖开"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    return self.sendOrderFAK(CTAORDER_SHORT, price, volume, symbol, exchange)


    # ----------------------------------------------------------------------


def cover_fak(self, price, volume, symbol='', exchange='', stop=False):
    """买平"""
    symbol = self.symbolList[0] if symbol == '' else symbol
    exchange = self.exchangeList[0] if exchange == '' else exchange
    tpos0S = self.tpos0S.get(symbol)
    ypos0S = self.ypos0S.get(symbol)
    if tpos0S >= volume:
        return self.sendOrderFAK(CTAORDER_COVER_TODAY, price, volume, symbol, exchange)
    elif ypos0S >= volume:
        return self.sendOrderFAK(CTAORDER_COVER, price, volume, symbol, exchange)


        # ----------------------------------------------------------------------


def sendOrder(self, orderType, price, volume, symbol, exchange, stop=False):
    """发送委托"""
    if self.trading:
        # 如果stop为True，则意味着发本地停止单
        req = {}
        req['sid'] = self.sid
        if orderType == CTAORDER_BUY:
            req['direction'] = '0'
            req['offset'] = '0'
        elif orderType == CTAORDER_SELL:
            req['direction'] = '1'
            req['offset'] = '1'
        elif orderType == CTAORDER_SELL_TODAY:
            req['direction'] = '1'
            req['offset'] = '3'
        elif orderType == CTAORDER_SHORT:
            req['direction'] = '1'
            req['offset'] = '0'
        elif orderType == CTAORDER_COVER:
            req['direction'] = '0'
            req['offset'] = '1'
        elif orderType == CTAORDER_COVER_TODAY:
            req['direction'] = '0'
            req['offset'] = '3'
        req['symbol'] = symbol
        req['volume'] = volume
        req['price'] = price
        req['hedgeflag'] = '1'
        req['ordertype'] = '0'
        req['exchange'] = exchange
        vtOrderID = ctaEngine.sendOrder(req)
        return vtOrderID
    else:
        return None

        # ----------------------------------------------------------------------


def sendOrderFOK(self, orderType, price, volume, symbol, exchange, stop=False):
    """发送委托"""
    if self.trading:
        # 如果stop为True，则意味着发本地停止单
        req = {}
        req['sid'] = self.sid
        if orderType == CTAORDER_BUY:
            req['direction'] = '0'
            req['offset'] = '0'
        elif orderType == CTAORDER_SELL:
            req['direction'] = '1'
            req['offset'] = '1'
        elif orderType == CTAORDER_SELL_TODAY:
            req['direction'] = '1'
            req['offset'] = '3'
        elif orderType == CTAORDER_SHORT:
            req['direction'] = '1'
            req['offset'] = '0'
        elif orderType == CTAORDER_COVER:
            req['direction'] = '0'
            req['offset'] = '1'
        elif orderType == CTAORDER_COVER_TODAY:
            req['direction'] = '0'
            req['offset'] = '3'
        req['symbol'] = symbol
        req['volume'] = volume
        req['price'] = price
        req['hedgeflag'] = '1'
        req['ordertype'] = '2'
        req['exchange'] = exchange
        vtOrderID = ctaEngine.sendOrder(req)
        return vtOrderID
    else:
        return None

        # ----------------------------------------------------------------------


def sendOrderFAK(self, orderType, price, volume, symbol, exchange, stop=False):
    """发送委托"""
    if self.trading:
        # 如果stop为True，则意味着发本地停止单
        req = {}
        req['sid'] = self.sid
        if orderType == CTAORDER_BUY:
            req['direction'] = '0'
            req['offset'] = '0'
        elif orderType == CTAORDER_SELL:
            req['direction'] = '1'
            req['offset'] = '1'
        elif orderType == CTAORDER_SELL_TODAY:
            req['direction'] = '1'
            req['offset'] = '3'
        elif orderType == CTAORDER_SHORT:
            req['direction'] = '1'
            req['offset'] = '0'
        elif orderType == CTAORDER_COVER:
            req['direction'] = '0'
            req['offset'] = '1'
        elif orderType == CTAORDER_COVER_TODAY:
            req['direction'] = '0'
            req['offset'] = '3'
        req['symbol'] = symbol
        req['volume'] = volume
        req['price'] = price
        req['hedgeflag'] = '1'
        req['ordertype'] = '1'
        req['exchange'] = exchange
        vtOrderID = ctaEngine.sendOrder(req)
        return vtOrderID
    else:
        return None

        # ----------------------------------------------------------------------





def cancelOrder(self, vtOrderID):
    """撤单"""
    return ctaEngine.cancelOrder(vtOrderID)


# ----------------------------------------------------------------------
def cancelOrderSyn(self, vtOrderID):
    """撤单"""
    return ctaEngine.cancelOrder(vtOrderID)


# ---------------------------------------------------------------------
def loadDay(self, years, symbol='', exchange=''):
    """载入日K线"""
    symbol = self.vtSymbol if symbol == '' else symbol
    exchange = self.exchange if exchange == '' else exchange
    url = 'http://122.144.129.233:60007/hismin?instrumentid={}&datatype=1&exchangeid={}&startday={}&secretkey=1&daynum={}&rtnnum=20'.format(
        symbol, exchange, datetime.datetime.now().strftime('%Y%m%d'), years)
    r = requests.post(url)
    try:
        l = json.loads(r.text)
        for d in reversed(l):
            bar = VtBarData()
            bar.vtSymbol = self.vtSymbol
            bar.symbol = self.vtSymbol
            bar.exchange = self.exchange

            bar.open = d['OpenPrice']
            bar.high = d['HighestPrice']
            bar.low = d['LowestPrice']
            bar.close = d['ClosePrice']
            bar.volume = d['Volume']
            bar.turnover = d['Turnover']
            bar.datetime = datetime.datetime.strptime(d['ActionDay'] + d['UpdateTime'], '%Y%m%d%H:%M:%S')
            self.onBar(bar)
    except:
        self.output(u'历史数据获取失败，使用实盘数据初始化')


# ---------------------------------------------------------------------
def loadBar(self, days, symbol='', exchange=''):
    """载入1分钟K线"""
    symbol = self.vtSymbol if symbol == '' else symbol
    exchange = self.exchange if exchange == '' else exchange
    url = 'http://122.144.129.233:60007/hismin?instrumentid={}&datatype=0&exchangeid={}&startday={}&secretkey=1&daynum={}&rtnnum=20'.format(
        symbol, exchange, datetime.datetime.now().strftime('%Y%m%d'), days)
    r = requests.post(url)
    try:
        l = json.loads(r.text)
        for d in reversed(l):
            bar = VtBarData()
            bar.vtSymbol = self.vtSymbol
            bar.symbol = self.vtSymbol
            bar.exchange = self.exchange

            bar.open = d['OpenPrice']
            bar.high = d['HighestPrice']
            bar.low = d['LowestPrice']
            bar.close = d['ClosePrice']
            bar.volume = d['Volume']
            bar.turnover = d['Turnover']
            bar.datetime = datetime.datetime.strptime(d['ActionDay'] + d['UpdateTime'], '%Y%m%d%H:%M:%S')
            self.onBar(bar)
    except:
        self.output(u'历史数据获取失败，使用实盘数据初始化')


# ---------------------------------------------------------------------
def loadTick(self, days):
    """载入Tick"""
    return []


# ----------------------------------------------------------------------
def getGui(self):
    """创建界面"""
    if not self.__class__.qtsp is None:
        self.__class__.qtsp.signal.emit(self)


# ----------------------------------------------------------------------
def closeGui(self):
    """创建界面"""
    if not self.__class__.qtsp is None:
        self.__class__.qtsp.signalc.emit(self)


# ----------------------------------------------------------------------
def getInvestorAccount(self, investorID):
    """输出信息"""
    return ctaEngine.getInvestorAccount(str(investorID))


# ----------------------------------------------------------------------
def getInvestorPosition(self, investorID):
    """输出信息"""
    return ctaEngine.getInvestorPosition(str(investorID))


# ----------------------------------------------------------------------
def output(self, content):
    """输出信息"""
    ctaEngine.writeLog(str(content))


# ----------------------------------------------------------------------
def writeCtaLog(self, content):
    """记录CTA日志"""
    content = self.name + ' : ' + content
    ctaEngine.writeLog(content)


# ----------------------------------------------------------------------
def putEvent(self):
    """发出策略状态变化事件"""
    setting = OrderedDict()
    setting['sid'] = self.sid
    for key in reversed(self.varList):
        if key in self.varMap:
            setting[self.varMap[key]] = str(getattr(self, key))
    ctaEngine.updateState(setting)


@classmethod
# ----------------------------------------------------------------------
def StartGui(cls):
    app = QtGui.QApplication([''])
    # 设置Qt的皮肤
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))
        basePath = os.path.split(os.path.realpath(__file__))[0]
        cfgfile = QtCore.QFile(basePath + '\css.qss')
        cfgfile.open(QtCore.QFile.ReadOnly)
        styleSheet = cfgfile.readAll()
        styleSheet = unicode(styleSheet, encoding='utf8')
        app.setStyleSheet(styleSheet)
    except:
        pass
    # 界面设置
    cls.qtsp = QtGuiSupport()
    # 在主线程中启动Qt事件循环
    sys.exit(app.exec_())
    cls.t = None


CtaTemplate.setQtSp()

########################################################################



class BarManager(object):
    """
    K线合成器，支持：
    1. 基于Tick合成1分钟K线
    2. 基于1分钟K线合成X分钟K线（X可以是2、3、5、10、15、30、60）
    """

    # ----------------------------------------------------------------------
    def __init__(self, onBar, xmin=0, onXminBar=None):
        """Constructor"""
        self.bar = None  # 1分钟K线对象
        self.onBar = onBar  # 1分钟K线回调函数

        self.xminBar = None  # X分钟K线对象
        self.xmin = xmin  # X的值
        self.onXminBar = onXminBar  # X分钟K线的回调函数

        self.lastTick = None  # 上一TICK缓存对象

        # ----------------------------------------------------------------------





def updateTick(self, tick):
    """TICK更新"""
    newMinute = False  # 默认不是新的一分钟

    # 尚未创建对象
    if not self.bar:
        self.bar = VtBarData()
        newMinute = True
    # 新的一分钟
    elif self.bar.datetime.minute != tick.datetime.minute:
        # 生成上一分钟K线的时间戳
        self.bar.datetime = self.bar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
        self.bar.date = self.bar.datetime.strftime('%Y%m%d')
        self.bar.time = self.bar.datetime.strftime('%H:%M:%S.%f')

        # 推送已经结束的上一分钟K线
        self.onBar(self.bar)

        # 创建新的K线对象
        self.bar = VtBarData()
        newMinute = True

    # 初始化新一分钟的K线数据
    if newMinute:
        self.bar.vtSymbol = tick.vtSymbol
        self.bar.symbol = tick.symbol
        self.bar.exchange = tick.exchange

        self.bar.open = tick.lastPrice
        self.bar.high = tick.lastPrice
        self.bar.low = tick.lastPrice
    # 累加更新老一分钟的K线数据
    else:
        self.bar.high = max(self.bar.high, tick.lastPrice)
        self.bar.low = min(self.bar.low, tick.lastPrice)

    # 通用更新部分
    self.bar.close = tick.lastPrice
    self.bar.datetime = tick.datetime
    self.bar.openInterest = tick.openInterest

    if self.lastTick:
        self.bar.volume += (tick.volume - self.lastTick.volume)  # 当前K线内的成交量

    # 缓存Tick
    self.lastTick = tick


    # ----------------------------------------------------------------------





def updateBar(self, bar):
    """1分钟K线更新"""
    # 尚未创建对象
    if not self.xminBar:
        self.xminBar = VtBarData()

        self.xminBar.vtSymbol = bar.vtSymbol
        self.xminBar.symbol = bar.symbol
        self.xminBar.exchange = bar.exchange

        self.xminBar.open = bar.open
        self.xminBar.high = bar.high
        self.xminBar.low = bar.low

        # 累加老K线
    else:
        self.xminBar.high = max(self.xminBar.high, bar.high)
        self.xminBar.low = min(self.xminBar.low, bar.low)

    # 通用部分
    self.xminBar.close = bar.close
    self.xminBar.datetime = bar.datetime
    self.xminBar.openInterest = bar.openInterest
    self.xminBar.volume += int(bar.volume)

    # X分钟已经走完
    if not bar.datetime.minute % self.xmin:  # 可以用X整除
        # 生成上一X分钟K线的时间戳
        self.xminBar.datetime = self.xminBar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
        self.xminBar.date = self.xminBar.datetime.strftime('%Y%m%d')
        self.xminBar.time = self.xminBar.datetime.strftime('%H:%M:%S.%f')

        # 推送
        self.onXminBar(self.xminBar)

        # 清空老K线缓存对象
        self.xminBar = None


########################################################################



class ArrayManager(object):
    """
    K线序列管理工具，负责：
    1. K线时间序列的维护
    2. 常用技术指标的计算
    """

    # ----------------------------------------------------------------------
    def __init__(self, size=100, maxsize=None, bars=None):
        """Constructor"""

        # 一次性载入
        if not bars is None:
            self.size = size
            self.maxsize = size if maxsize is None else maxsize
            return self.loadBars(bars)

        # 实盘分次载入
        self.count = 0  # 缓存计数
        self.size = size  # 缓存大小
        self.inited = False  # True if count>=size

        self.maxsize = size if maxsize is None else maxsize

        self.openArray = np.zeros(self.maxsize)  # OHLC
        self.highArray = np.zeros(self.maxsize)
        self.lowArray = np.zeros(self.maxsize)
        self.closeArray = np.zeros(self.maxsize)
        self.volumeArray = np.zeros(self.maxsize)

        # ----------------------------------------------------------------------





def updateBar(self, bar):
    """更新K线"""
    self.count += 1
    if not self.inited and self.count >= self.size:
        self.inited = True
    self.openArray[0:self.maxsize - 1] = self.openArray[1:self.maxsize]
    self.highArray[0:self.maxsize - 1] = self.highArray[1:self.maxsize]
    self.lowArray[0:self.maxsize - 1] = self.lowArray[1:self.maxsize]
    self.closeArray[0:self.maxsize - 1] = self.closeArray[1:self.maxsize]
    self.volumeArray[0:self.maxsize - 1] = self.volumeArray[1:self.maxsize]

    self.openArray[-1] = bar.open
    self.highArray[-1] = bar.high
    self.lowArray[-1] = bar.low
    self.closeArray[-1] = bar.close
    self.volumeArray[-1] = bar.volume
    return self.inited


# ----------------------------------------------------------------------
@property
def open(self):
    """获取开盘价序列"""
    return self.openArray[-self.size:]


# ----------------------------------------------------------------------
@property
def high(self):
    """获取最高价序列"""
    return self.highArray[-self.size:]


# ----------------------------------------------------------------------
@property
def low(self):
    """获取最低价序列"""
    return self.lowArray[-self.size:]


# ----------------------------------------------------------------------
@property
def close(self):
    """获取收盘价序列"""
    return self.closeArray[-self.size:]


# ----------------------------------------------------------------------
@property
def volume(self):
    """获取成交量序列"""
    return self.volumeArray[-self.size:]

    # ----------------------------------------------------------------------





def sma(self, n, array=False):
    """简单均线"""
    result = talib.SMA(self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def std(self, n, array=False):
    """标准差"""
    result = talib.STDDEV(self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def cci(self, n, array=False):
    """CCI指标"""
    result = talib.CCI(self.high, self.low, self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def kd(self, nf=9, ns=3, array=False):
    """KD指标"""
    slowk, slowd = talib.STOCH(self.high, self.low, self.close,
                               fastk_period=nf,
                               slowk_period=ns,
                               slowk_matype=0,
                               slowd_period=ns,
                               slowd_matype=0)
    if array:
        return slowk, slowd
    return slowk[-1], slowd[-1]


    # ----------------------------------------------------------------------





def atr(self, n, array=False):
    """ATR指标"""
    result = talib.ATR(self.high, self.low, self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def rsi(self, n, array=False):
    """RSI指标"""
    result = talib.RSI(self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def macd(self, fastPeriod, slowPeriod, signalPeriod, array=False):
    """MACD指标"""
    macd, signal, hist = talib.MACD(self.close, fastPeriod,
                                    slowPeriod, signalPeriod)
    if array:
        return macd, signal, hist
    return macd[-1], signal[-1], hist[-1]


    # ----------------------------------------------------------------------





def adx(self, n, array=False):
    """ADX指标"""
    result = talib.ADX(self.high, self.low, self.close, n)
    if array:
        return result
    return result[-1]


    # ----------------------------------------------------------------------





def peak(self, lookahead=100, delta=5, array=False):
    """峰值"""
    size = min(self.count, self.maxsize - 1)
    maxP, minP = peakdetect(self.closeArray[-size:], lookahead=lookahead, delta=delta)
    if array:
        return maxP, minP
    return maxP, minP


    # ----------------------------------------------------------------------





def boll(self, n, dev, array=False):
    """布林通道"""
    mid = self.sma(n, array)
    std = self.std(n, array)

    up = mid + std * dev
    down = mid - std * dev

    return up, down


    # ----------------------------------------------------------------------





def keltner(self, n, dev, array=False):
    """肯特纳通道"""
    mid = self.sma(n, array)
    atr = self.atr(n, array)

    up = mid + atr * dev
    down = mid - atr * dev

    return up, down


    # ----------------------------------------------------------------------




def donchian(self, n, array=False):
    """唐奇安通道"""
    up = talib.MAX(self.high, n)
    down = talib.MIN(self.low, n)

    if array:
        return up, down
    return up[-1], down[-1]


########################################################################
class QtGuiSupport(QtCore.QObject):
    """支持QT的对象类"""

    signal = QtCore.pyqtSignal(object)
    signalc = QtCore.pyqtSignal(object)

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(QtGuiSupport, self).__init__()
        self.widgetDict = {}
        self.signal.connect(self.showStrategyWidget)
        self.signalc.connect(self.closeStrategyWidget)
        self.w = QtGui.QWidget()
        self.w.hide()

    # ----------------------------------------------------------------------
    def showStrategyWidget(self, s):
        if not s.widgetClass is None:
            if self.widgetDict.get(s.name) is None:
                s.widget = s.widgetClass(s)
                self.widgetDict[s.name] = s.widget
                s.widget.show()
            else:
                self.widgetDict[s.name].show()

    # ----------------------------------------------------------------------
    def closeStrategyWidget(self, s):
        if not s.widgetClass is None:
            if self.widgetDict.get(s.name) is None:
                return
            else:
                self.widgetDict[s.name].hide()


from PyQt4.QtCore import Qt
from PyQt4 import QtGui, QtCore
from uiKLine import *
import pandas as pd
from collections import defaultdict

# 字符串转换
# ---------------------------------------------------------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

########################################################################



class KLWidget(QtGui.QWidget):
    """简单交易组件"""

    signalBar = QtCore.pyqtSignal(type({}))
    signalLoad = QtCore.pyqtSignal()

    # ----------------------------------------------------------------------
    def __init__(self, strategy, parent=None):
        """Constructor"""
        super(KLWidget, self).__init__(parent)
        self.strategy = strategy
        self.symbol = ''
        self.started = True
        self.bar = None
        self.mainSigs = strategy.mainSigs
        self.subSigs = strategy.subSigs
        self.initUi()
        self.bars = []
        self.sigs = []
        self.stateData = defaultdict(list)
        self.signalBar.connect(self.updateBar)
        self.signalLoad.connect(self.loadBar)

        # ----------------------------------------------------------------------





def initUi(self):
    """初始化界面"""
    # 设置标题
    s = self.strategy
    self.setWindowTitle(u'策略-{}'.format(s.name))
    self.uiKLine = KLineWidget(self)

    # 整合布局
    vbox = QtGui.QVBoxLayout()
    vbox.addWidget(self.uiKLine)
    self.setLayout(vbox)

    self.setFixedSize(750, 850);


    # ----------------------------------------------------------------------





def addBar(self, data):
    """策略未启动新增行情"""
    try:
        if self.strategy.trading:
            self.signalBar.emit(data)
        else:
            bar = data['bar']
            sig = data['sig']
            self.bars.append(bar.__dict__)
            self.sigs.append(sig)
            for s in (self.mainSigs + self.subSigs):
                self.stateData[s].append(data[s])
    except Exception as e:
        self.strategy.output(str(e))
        self.strategy.output(str(traceback.format_exc()))


        # ----------------------------------------------------------------------





def updateBar(self, data):
    """更新行情"""
    bar = data['bar']
    sig = data['sig']
    # 清空价格数量
    try:
        if self.bar is None or (not bar.datetime == self.bar.datetime):
            if self.strategy.trading:
                self.bars.append(bar.__dict__)
                self.sigs.append(sig)
                for s in (self.mainSigs + self.subSigs):
                    self.stateData[s].append(data[s])
                self.uiKLine.onBar(bar, sig)
                for s in self.mainSigs:
                    self.plotMain(s)
                for s in self.subSigs:
                    self.plotSub(s)
                self.uiKLine.updateSig(self.sigs)
        self.bar = bar
    except Exception as e:
        self.strategy.output(str(e))
        self.strategy.output(str(traceback.format_exc()))


        # ----------------------------------------------------------------------




def loadBar(self):
    """载入历史K线数据"""
    pdData = pd.DataFrame(self.bars).set_index('datetime')
    self.uiKLine.loadData(pdData)
    for s in self.mainSigs:
        self.plotMain(s)
    for s in self.subSigs:
        self.plotSub(s)
    self.uiKLine.updateSig(self.sigs)
    self.bar = self.strategy.bar


    # ----------------------------------------------------------------------





def clear(self):
    """清空数据"""
    self.bars = []
    self.sigs = []
    self.stateData = defaultdict(list)
    self.uiKLine.clearData()
    self.uiKLine.clearSig()
    self.started = False


    # ----------------------------------------------------------------------





def plotSub(self, sigName):
    """输出信号到副图"""
    self.uiKLine.datas['openInterest'] = np.array(self.stateData[sigName])
    self.uiKLine.listOpenInterest = copy.copy(self.stateData[sigName])
    self.uiKLine.showSig({sigName: np.array(self.stateData[sigName])}, False)


    # ----------------------------------------------------------------------





def plotMain(self, sigName):
    """输出信号到主图"""
    if sigName in self.uiKLine.sigData:
        self.uiKLine.sigData[sigName] = np.array(self.stateData[sigName])
        self.uiKLine.sigPlots[sigName].setData(np.array(self.stateData[sigName]), pen=self.uiKLine.sigColor[sigName][0],
                                               name=sigName)
    else:
        self.uiKLine.showSig({sigName: np.array(self.stateData[sigName])}, True)


        # ----------------------------------------------------------------------





def closeEvent(self, evt):
    """关闭"""
    s = self.strategy
    if s.trading == False:
        evt.accept()
    else:
        s.output(u'只能在停止策略时自动关闭')
    evt.ignore()