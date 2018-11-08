#!/usr/bin/python
# coding:utf-8

"""
@author: Miaohua.L
@contact: miaohua.l@bitpower.com.cn
@file: turtle_strategy.py
@time: 2018/9/21 20:54
"""
import sys
import numpy as np
import pandas as pd

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)
from atrader import *
import numpy as np
from datetime import datetime, date


# 初始化设置
def init(context):
    set_backtest(initial_cash=10000000, margin_rate=1.0, slide_price=0.0,
                 price_loc=1, deal_type=0, limit_type=0)  # 设置回测初始资金信息
    context.TLen = len(context.target_list)  # 标的个数
    reg_kdata('min', 1)  # 注册k线数据
    context.N = 101  # k线长度

    # context.parameter分别为唐奇安开仓通道.唐奇安平仓通道.短ma.长ma.ATR的参数
    context.parameter = [55, 20, 10, 60, 20]
    context.tar = context.parameter[4]


# 策略逻辑
def on_data(context):
    mp = context.account().positions  # 获取当前仓位
    bar = get_current_bar()
    kdata = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N, fill_up=True, df=True)  # 获取k线数据
    for i in range(context.TLen):
        df = kdata[kdata['target_idx'] == i]
        high1 = df['high'].astype(float)  # high价
        low1 = df['low'].astype(float)  # low价
        close1 = df['close'].astype(float)  # close价
        if np.isnan(close1.iloc[0]) == 1:
            return  # 无数据跳过

        close = close1.values[-1]
        # 计算ATR
        atr = talib.ATR(high1.values, low1.values, close1.values, timeperiod=context.tar)[-1]
        # 计算唐奇安开仓和平仓通道
        context.don_open = context.parameter[0] + 1
        upper_band = talib.MAX(close1.values[:-1], timeperiod=context.don_open)[-1]
        context.don_close = context.parameter[1] + 1
        lower_band = talib.MIN(close1.values[:-1], timeperiod=context.don_close)[-1]
        # 若没有仓位则开仓
        position_long = mp.loc[i, 'volume_long']
        position_short = mp.loc[i, 'volume_short']

        if not position_long and not position_short:
            # 计算长短ma线.DIF
            ma_short = talib.MA(close1.values, timeperiod=(context.parameter[2] + 1))[-1]
            ma_long = talib.MA(close1.values, timeperiod=(context.parameter[3] + 1))[-1]
            dif = ma_short - ma_long
            # 获取当前价格
            # 上穿唐奇安通道且短ma在长ma上方则开多仓
            if close > upper_band and (dif > 0):
                # order_target_volume(symbol=symbol, volume=8, position_side=PositionSide_Long, order_type=OrderType_Market)
                order_volume(account_idx=0, target_idx=i, volume=8, side=1, position_effect=1, order_type=2, price=0)
                print(context.target_list[i], '市价单开多仓8手')
            # 下穿唐奇安通道且短ma在长ma下方则开空仓
            if close < lower_band and (dif < 0):
                # order_target_volume(symbol=symbol, volume=8, position_side=PositionSide_Short, order_type=OrderType_Market)
                order_volume(account_idx=0, target_idx=i, volume=8, side=2, position_effect=1, order_type=2, price=0)
                print(context.target_list[i], '市价单开空仓8手')
        elif position_long:
            # 价格跌破唐奇安平仓通道全平仓位止损
            if close < lower_band:
                order_close_all()
                print(context.target_list[i], '市价单全平仓位')
            else:
                vwap = mp.loc[i, 'holding_cost_long']
                # 获取平仓的区间
                band = vwap - np.array([200, 2, 1.5, 1, 0.5, -100]) * atr
                # 计算最新应持仓位
                grid_volume = int(pd.cut(close1, band, labels=[0, 1, 2, 3, 4])[-1]) * 2
                if grid_volume > position_long:
                    order_volume(account_idx=0, target_idx=i, volume=grid_volume - position_long, side=1,
                                 position_effect=1, order_type=2, price=0)
                else:
                    order_volume(account_idx=0, target_idx=i, volume=position_long - grid_volume, side=2,
                                 position_effect=2, order_type=2, price=0)
                print(context.target_list[i], '市价单平多仓到', grid_volume, '手')
        elif position_short:
            # 价格涨破唐奇安平仓通道或价格涨破持仓均价加两倍ATR平空仓
            if close > upper_band:
                order_close_all()
                print(context.target_list[i], '市价单全平仓位')
            else:
                # 获取持仓均价
                vwap = mp.loc[i, 'holding_cost_short']
                # 获取平仓的区间
                band = vwap + np.array([-100, 0.5, 1, 1.5, 2, 200]) * atr
                # 计算最新应持仓位
                grid_volume = int(pd.cut(close1, band, labels=[0, 1, 2, 3, 4])[-1]) * 2
                if grid_volume > position_short:
                    order_volume(account_idx=0, target_idx=i, volume=grid_volume - position_short, side=2,
                                 position_effect=1, order_type=2, price=0)
                else:
                    order_volume(account_idx=0, target_idx=i, volume=position_short - grid_volume, side=1,
                                 position_effect=2, order_type=2, price=0)
                print(context.target_list[i], '市价单平空仓到', grid_volume, '手')


if __name__ == '__main__':
    target_list = ['CZCE.FG000', 'SHFE.rb0000']  # 设置回测标的
    frequency = 'min'  # 设置刷新频率
    fre_num = 1  # 设置刷新频率
    begin_date = '2017-06-01'  # 设置回测初始时间
    end_date = '2017-09-01'  # 设置回测结束时间
    fq = 1  # 设置复权方式
    run_backtest('海龟', '海龟.py', target_list=target_list, frequency=frequency, fre_num=fre_num,
                 begin_date=begin_date, end_date=end_date, fq=fq)
