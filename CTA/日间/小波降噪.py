# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     小波降噪
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
import pywt
from atrader import *
import numpy as np
import sys

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)


def init(context):
    set_backtest(initial_cash=10000000)
    reg_kdata('min', 30)
    context.N = 30
    context.n1 = 5
    context.n2 = 20
    context.initial = 10000000
    context.barlength = 420


def wave(array):
    coeffs = pywt.wavedec(array, 'haar', level=2)
    coeffs[-1], coeffs[-2] = np.zeros_like(coeffs[-1]), np.zeros_like(coeffs[-2])
    ss = pywt.waverec(coeffs, 'haar')
    return ss[-1]


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.barlength, fill_up=True, df=True)  # 获取所有标的数据
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    close = data.close
    s1 = close.rolling(102).apply(wave)
    dif, dea, macd = talib.MACD(s1, fastperiod=12, slowperiod=26, signalperiod=9)
    ma1 = talib.EMA(s1, context.n1)
    ma2 = talib.EMA(s1, context.n2)
    condi_long = macd.iloc[-1] > 0 and ma1.iloc[-1] > ma2.iloc[-1]  # 开多平空条件
    condi_short = macd.iloc[-1] < 0 and ma1.iloc[-1] < ma2.iloc[-1]  # 开空平多条件
    if condi_long and long_positions[0] == 0:  # 开多仓
        order_target_value(account_idx=0, target_idx=0, target_value=context.initial, side=1, order_type=2)
    if condi_short and short_positions[0] == 0:  # 开空仓
        order_target_value(account_idx=0, target_idx=0, target_value=context.initial, side=2, order_type=2)
    if condi_short and long_positions[0] > 0:  # 平多仓
        order_target_volume(account_idx=0, target_idx=0, target_volume=0, side=1, order_type=2)
    if condi_long and short_positions[0] > 0:  # 平空仓
        order_target_volume(account_idx=0, target_idx=0, target_volume=0, side=2, order_type=2)


if __name__ == '__main__':
    target = ['cffex.if0000']
    run_backtest('小波降噪', '小波降噪.py', target_list=target, frequency='min', fre_num=30, begin_date='2017-06-01',
                 end_date='2018-06-01', fq=1)
