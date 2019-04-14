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

# k_lines_pump = KLinesPump()
#
# k_lines_pump.process_data(depth_market_data=some_one, interval=some_number)


