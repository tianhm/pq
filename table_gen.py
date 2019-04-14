#-*- coding:utf-8 -*-
import sqlite3
import time
from FinalLogger import logger
from Constant import inst_strategy, database_map, suffix_list

conn = sqlite3.connect('futures.db3', check_same_thread = False)
# init database and read data to memory
table_list = ['j1805','rb1805','rb1810']
# for i in inst_strategy.keys() :
for i in table_list:
    # create table if not exist
    cmd = "CREATE TABLE IF NOT EXISTS " + i + suffix_list[0]\
          + " (id INTEGER PRIMARY KEY NULL, inst TEXT NULL, open DOUBLE NULL, high DOUBLE NULL, low DOUBLE NULL, close DOUBLE NULL, volume INTEGER NULL, TradingDay TEXT NULL, time TEXT NULL)"
    conn.execute(cmd)

    cmd = "CREATE TABLE IF NOT EXISTS " + i + suffix_list[1] \
          + " (id INTEGER PRIMARY KEY NULL, inst TEXT NULL, OrderRef TEXT NULL, Direction TEXT NULL, OffsetFlag TEXT NULL, Price DOUBLE NULL, Volume INTEGER NULL, TradeDate TEXT NULL, TradeTime TIME NULL )"
    conn.execute(cmd)

    cmd = "CREATE TABLE IF NOT EXISTS " + i + suffix_list[2] \
          + " (id INTEGER PRIMARY KEY NULL, inst TEXT NULL, OrderRef TEXT NULL, Direction TEXT NULL, OffsetFlag TEXT NULL, Price DOUBLE NULL, Volume INTEGER NULL, TradeDate TEXT NULL, TradeTime TIME NULL )"
    conn.execute(cmd)

    conn.commit()

