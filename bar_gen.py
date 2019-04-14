#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import json


__author__ = 'James Iter'
__date__ = '2018/3/27'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


class barPump(object):

    def __init__(self):
        self.k_lines = dict()
        self.k_lines_list = dict()
        self.last_ts_step = dict()

    def process_data(self, depth_market_data=None, interval=60, save_dir_path=None):
        """
        :param depth_market_data:
        :param interval: 单位(秒)
        :param save_dir_path: 文件存储目录路径
        :return:
        """
        for key in ['InstrumentID', 'LastPrice', 'TradingDay', 'UpdateTime']:
            if not hasattr(depth_market_data, key):
                return

        date_time = ' '.join([depth_market_data.TradingDay, depth_market_data.UpdateTime])
        instrument_id = depth_market_data.InstrumentID
        ts_step = int(time.mktime(time.strptime(date_time, "%Y%m%d %H:%M:%S"))) / interval

        if instrument_id not in self.last_ts_step:
            self.last_ts_step[instrument_id] = ''

        if self.last_ts_step[instrument_id] != ts_step:
            # 此处可以处理一些边界操作。比如对上一个区间的值做特殊处理等。
            print type(self.last_ts_step[instrument_id]), self.last_ts_step[instrument_id]
            key_instrument_id_last_ts_step = '_'.join([instrument_id, self.last_ts_step[instrument_id].__str__()])

            if key_instrument_id_last_ts_step not in self.k_lines_list:
                self.k_lines_list[key_instrument_id_last_ts_step] = list()

            if key_instrument_id_last_ts_step in self.k_lines:
                self.k_lines_list[key_instrument_id_last_ts_step].append(self.k_lines[key_instrument_id_last_ts_step])

                if save_dir_path is not None:
                    file_name = '_'.join([instrument_id, depth_market_data.TradingDay,
                                          interval.__str__()]) + '.json'
                    save_path = '/'.join([save_dir_path, file_name])

                    with open(save_path, 'a') as f:
                        f.writelines(json.dumps(
                            self.k_lines[key_instrument_id_last_ts_step], ensure_ascii=False) + '\n')

            self.last_ts_step[instrument_id] = ts_step

        last_price = depth_market_data.LastPrice

        key_instrument_id_ts_step = '_'.join([instrument_id,ts_step.__str__()])

        if key_instrument_id_ts_step not in self.k_lines:
            self.k_lines[key_instrument_id_ts_step] = {
                'open': last_price,
                'high': last_price,
                'low': last_price,
                'close': last_price,
                'date_time': date_time,
                'instrument_id': instrument_id
            }

        self.k_lines[key_instrument_id_ts_step]['close'] = last_price

        if last_price > self.k_lines[key_instrument_id_ts_step]['high']:
            self.k_lines[key_instrument_id_ts_step]['high'] = last_price

        elif last_price < self.k_lines[key_instrument_id_ts_step]['low']:
            self.k_lines[key_instrument_id_ts_step]['low'] = last_price

        else:
            pass


# 为每个周期，或每个线程，创建单独的实例
k_lines_pump_interval_60 = barPump()
k_lines_pump_interval_300 = barPump()
k_lines_pump_interval_3600 = barPump()


def the_method():
    k_lines_pump_interval_60.process_data(depth_market_data=the_data, interval=60, save_dir_path=the_dir_path)
    k_lines_pump_interval_300.process_data(depth_market_data=the_data, interval=300, save_dir_path=the_dir_path)
    k_lines_pump_interval_3600.process_data(depth_market_data=the_data, interval=3600, save_dir_path=the_dir_path)



