#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'James Iter'
__date__ = '2018/3/27'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


k_lines = dict()
k_lines_list = list()
last_date_time = ''


def process_data(depth_market_data=None, interval='m'):
    """
    :param depth_market_data:
    :param interval: ['d' | 'h' | 'm'] 分别对应 '日'，'时'，'分'
    :return:
    """
    global last_date_time

    for key in ['LastPrice', 'TradingDay', 'UpdateTime']:
        if not hasattr(depth_market_data, key):
            return

    date_time = ''

    if interval == 'd':
        date_time = depth_market_data.TradingDay

    elif interval == 'h':
        date_time = ' '.join([depth_market_data.TradingDay,
                              depth_market_data.UpdateTime[:depth_market_data.UpdateTime.find(':')]])

    elif interval == 'm':
        date_time = ' '.join([depth_market_data.TradingDay,
                              depth_market_data.UpdateTime[:depth_market_data.UpdateTime.rfind(':')]])

    else:
        pass

    if last_date_time != date_time:
        # 此处可以处理一些边界操作。比如对上一个区间的值做特殊处理等。

        if last_date_time in k_lines:
            k_lines_list.append(k_lines[last_date_time])

        last_date_time = date_time

    last_price = depth_market_data.LastPrice

    if date_time not in k_lines:
        k_lines[date_time] = {
            'open': last_price,
            'high': last_price,
            'low': last_price,
            'close': last_price
        }

    k_lines[date_time]['close'] = last_price

    if last_price > k_lines[date_time]['high']:
        k_lines[date_time]['high'] = last_price

    elif last_price < k_lines[date_time]['low']:
        k_lines[date_time]['low'] = last_price

    else:
        pass


