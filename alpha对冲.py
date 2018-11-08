# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     alpha对冲(股票+期货）
   Description :
   Author :       haoyuan.m
   date：          2018/10/12
-------------------------------------------------
   Change Activity:
                   2018/10/12:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
'''
本策略每隔1个月定时触发计算SHSE.000300成份股的过去一天EV/EBITDA值并选取30只EV/EBITDA值最小且大于零的股票
对不在股票池的股票平仓并等权配置股票池的标的
并用相应的CFFEX.IF对应的真实合约等额对冲
回测数据为:SHSE.000300和他们的成份股和CFFEX.IF对应的真实合约
回测时间为:2017-07-01 08:00:00到2017-10-01 16:00:00
'''
from atrader import *
import numpy as np
import pandas as pd
import datetime as dt
#%%
def init(context):
    # 设置开仓在股票和期货的资金百分比(期货在后面自动进行杠杆相关的调整)
    context.percentage_stock = 0.4
    context.percentage_futures = 0.4


def on_data(context):
    df = get_current_bar(target_indices=[])
    df = get_code_list('cffex', '2018-01-01')
    test = get_main_contract('cffex.if0000', begin_date='2018-05-05', end_date='2018-09-10')


if __name__ == '__main__':
    begin = '2017-09-01'
    end = '2018-09-30'
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    hs300 = get_code_list('hs300', cons_date)[['code', 'weight']]
    targetlist = hs300[hs300.weight > 0.35]['code']
    run_backtest(strategy_name='alpha',
                 file_path='alpha对冲.py',
                 target_list=targetlist,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)