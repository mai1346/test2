# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     网格交易
   Description :
   Author :       haoyuan.m
   date：          2018/10/22
-------------------------------------------------
   Change Activity:
                   2018/10/22:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
'''
本策略首先计算了rb1801过去300个1min收盘价的均值和标准差
并用均值加减2和3个标准差得到网格的区间分界线,分别配以0.3和0.5的仓位权重
然后根据价格所在的区间来配置仓位:
(n+k1*std,n+k2*std],(n+k2*std,n+k3*std],(n+k3*std,n+k4*std],(n+k4*std,n+k5*std],(n+k5*std,n+k6*std]
(n为收盘价的均值,std为收盘价的标准差,k1-k6分别为[-40, -3, -2, 2, 3, 40],其中-40和40为上下界,无实际意义)
[-0.5, -0.3, 0.0, 0.3, 0.5](资金比例,此处负号表示开空仓)
回测数据为:rb1801的1min数据
回测时间为:2017-07-01 08:00:00到2017-10-01 16:00:00
'''
from atrader import *
import numpy as np
import pandas as pd
import datetime as dt

def init(context):
    set_backtest(initial_cash=10000000)
    # 订阅rb1801, bar频率为1min
    reg_kdata('min', 1)
    # 获取过去300个价格数据
    hist_300bar = get_kdata_n('shfe.rb1801', 'min', 1, 300, end_date='2017-07-01', fill_up=True, df=True).close.values
    # 获取网格区间分界线
    context.band = np.mean(hist_300bar) + np.array([-10000, -3, -2, 2, 3, 10000]) * np.std(hist_300bar)
    # 设置网格的仓位
    context.weight = np.array([0.5, 0.3, 0.0, 0.3, 0.5]) * 10


def on_data(context):
    bar = get_current_bar()
    # 根据价格落在(-40,-3],(-3,-2],(-2,2],(2,3],(3,40]的区间范围来获取最新收盘价所在的价格区间
    grid = pd.cut(bar.close.values, context.band, labels=[0, 1, 2, 3, 4])[0]
    mktvalue = context.account().cash['total_value'].iloc[0]
    # 获取多仓仓位
    position_long = context.account().positions['volume_long'][0]
    # 获取空仓仓位
    position_short = context.account().positions['volume_short'][0]
    # 若无仓位且价格突破则按照设置好的区间开仓
    if not position_long and not position_short and grid != 2:
        # 大于3为在中间网格的上方,做多
        if grid >= 3:
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=1, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=1, order_type=2)
            print(context.now, context.target_list[0], '以市价单开多仓到仓位', context.weight[grid])
        elif grid <= 1:
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=2, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=2, order_type=2)
            print(context.now, context.target_list[0], '以市价单开空仓到仓位', context.weight[grid])
    # 持有多仓的处理
    elif position_long:
        if grid >= 3:
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=1, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=1, order_type=2)
            print(context.now, context.target_list[0], '以市价单调多仓到仓位', context.weight[grid])
        # 等于2为在中间网格,平仓
        elif grid == 2:
            order_target_value(account_idx=0, target_idx=0, target_value=0, side=1, order_type=2)
            print(context.now, context.target_list[0], '以市价单全平多仓')
        # 小于1为在中间网格的下方,做空
        elif grid <= 1:
            order_target_value(account_idx=0, target_idx=0, target_value=0, side=1, order_type=2)
            print(context.now, context.target_list[0], '以市价单全平多仓')
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=2, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=2, order_type=2)
            print(context.now, context.target_list[0], '以市价单开空仓到仓位', context.weight[grid])
    # 持有空仓的处理
    elif position_short:
        # 小于1为在中间网格的下方,做空
        if grid <= 1:
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=2, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=2, order_type=2)
            print(context.now, context.target_list[0], '以市价单调空仓到仓位', context.weight[grid])
        # 等于2为在中间网格,平仓
        elif grid == 2:
            order_target_value(account_idx=0, target_idx=0, target_value=0, side=0, order_type=2)
            print(context.now, context.target_list[0], '以市价单全平空仓')
        # 大于3为在中间网格的上方,做多
        elif grid >= 3:
            order_target_value(account_idx=0, target_idx=0, target_value=0, side=2, order_type=2)
            print(context.now, context.target_list[0], '以市价单全平空仓')
            order_target_value(account_idx=0, target_idx=0, target_value=mktvalue * context.weight[grid], side=1, order_type=2)
            # order_target_percent(account_idx=0, target_idx=0, target_percent=context.weight[grid], side=1, order_type=2)
            print(context.now, context.target_list[0], '以市价单开多仓到仓位', context.weight[grid])
    if context.now == dt.datetime(2017, 7, 27, 14, 11, 0):
        print('哈哈哈')

if __name__ == '__main__':
    targetlist = ['shfe.rb1801']
    run_backtest(strategy_name='网格交易',
                 file_path='网格交易.py',
                 target_list=targetlist,
                 frequency='min',
                 fre_num=1,
                 begin_date='2017-07-01',
                 end_date='2017-10-01',
                 fq=1)


