# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     日内回转交易
   Description :
   Author :       haoyuan.m
   date：          2018/10/16
-------------------------------------------------
   Change Activity:
                   2018/10/16:
-------------------------------------------------
"""

__author__ = 'haoyuan.m'

'''
本策略首先买入SHSE.600000股票10000股
随后根据60s的数据计算MACD(12,26,9),
在MACD>0的时候买入100股;在MACD<0的时候卖出100股
但每日操作的股票数不超过原有仓位,并于收盘前把仓位调整至开盘前的仓位
回测数据为:SHSE.600000的60s数据
回测时间为:2017-09-01 08:00:00到2017-10-01 16:00:00
'''

from atrader import *
import numpy as np
import pandas as pd
import datetime as dt
import sys

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)


def init(context):
    # 用于判定第一个仓位是否成功开仓
    context.first = 0
    set_backtest(initial_cash=100000, stock_cost_fee=0.1)
    reg_kdata('min', 1)
    # 日内回转每次交易100股
    context.trade_n = 100
    # 获取昨今天的时间
    context.day = [0, 0]
    # 用于判断是否触发了回转逻辑的计时
    context.ending = 0
    # 需要保持的总仓位
    context.total = 10000

def on_data(context):
    bar = get_current_bar()
    if context.first == 0:
        # 最开始配置仓位
        # 购买10000股浦发银行股票
        order_volume(account_idx=0, target_idx=0, volume=context.total, side=1, position_effect=1, order_type=2,
                     price=0)
        print(context.now, context.target_list[0], '以市价单开多仓10000股')
        context.first = 1.
        day = bar.time_bar.iloc[0]
        context.day[-1] = day.day
        # 每天的仓位操作
        context.turnaround = [0, 0]
        return

    # 更新最新的日期
    day = bar.time_bar.iloc[0]
    context.day[0] = day.day
    # 若为新的一天,则重置标记信息。
    if context.day[0] != context.day[-1]:
        context.ending = 0
        context.turnaround = [0, 0]
    # 如果一天结束，则
    if context.ending == 1:
        return
    # 若有可用的昨仓则操作
    if context.total >= 0:
        # 获取时间序列数据
        recent_data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=35, fill_up=True, df=True).close
        if recent_data.isna().any():
            return
        macd = talib.MACD(recent_data.astype(float))[2].iloc[-1]
        # 根据MACD>0则开仓,小于0则平仓
        if macd > 0:

            # 多空单向操作都不能超过昨仓位,否则最后无法调回原仓位
            if (context.turnaround[0] + context.trade_n) < context.total:
                # 计算累计仓位
                context.turnaround[0] += context.trade_n
                order_volume(account_idx=0, target_idx=0, volume=context.trade_n, side=1, position_effect=1,
                             order_type=2, price=0)
                print(context.now, context.target_list[0], '市价单开多仓', context.trade_n, '股')
        elif macd < 0:
            if (context.turnaround[1] + context.trade_n) < context.total:
                context.turnaround[1] += context.trade_n
                order_volume(account_idx=0, target_idx=0, volume=context.trade_n, side=2, position_effect=2,
                             order_type=2, price=0)
                print(context.now, context.target_list[0], '市价单平多仓', context.trade_n, '股')
        # 临近收盘时若仓位数不等于昨仓则回转所有仓位
        if (day.strftime('%Y-%m-%d %H:%M:%S')[11:16] == '14:55') or (
                day.strftime('%Y-%m-%d %H:%M:%S')[11:16] == '14:57'):
            position = context.account().positions['volume_long'][0]
            if position != context.total:
                order_target_volume(account_idx=0, target_idx=0, target_volume=context.total, side=1,
                                    order_type=2, price=0)
                print('市价单回转仓位操作...')
                context.ending = 1
        # 更新过去的日期数据
        context.day[-1] = context.day[0]


if __name__ == '__main__':
    recent_data = ['SSE.600000']
    run_backtest('日内回转交易', '日内回转交易.py', target_list=recent_data, frequency='min', fre_num=1, begin_date='2018-08-01',
                 end_date='2018-10-01', fq=1)
