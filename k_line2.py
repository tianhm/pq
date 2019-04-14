#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time


__author__ = 'James Iter'
__date__ = '2018/3/27'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


k_lines = dict()
k_lines_list = list()
last_ts_step = ''


def process_data(depth_market_data=None, interval=60):
    """
    :param depth_market_data:
    :param interval: 单位(秒)
    :return:
    """
    global last_ts_step

    for key in ['LastPrice', 'TradingDay', 'UpdateTime']:
        if not hasattr(depth_market_data, key):
            return

    date_time = ' '.join([depth_market_data.TradingDay, depth_market_data.UpdateTime])
    ts_step = int(time.mktime(time.strptime(date_time, "%Y%m%d %H:%M:%S"))) / interval

    print last_ts_step, ts_step
    if last_ts_step != ts_step:
        # 此处可以处理一些边界操作。比如对上一个区间的值做特殊处理等。

        if last_ts_step in k_lines:
            k_lines_list.append(k_lines[last_ts_step])
            print k_lines[last_ts_step]

        last_ts_step = ts_step

    last_price = depth_market_data.LastPrice

    if ts_step not in k_lines:
        k_lines[ts_step] = {
            'open': last_price,
            'high': last_price,
            'low': last_price,
            'close': last_price,
            'date_time': date_time
        }

    k_lines[ts_step]['close'] = last_price

    if last_price > k_lines[ts_step]['high']:
        k_lines[ts_step]['high'] = last_price

    elif last_price < k_lines[ts_step]['low']:
        k_lines[ts_step]['low'] = last_price

    else:
        pass


