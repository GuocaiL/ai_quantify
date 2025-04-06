from datetime import datetime
import pandas as pd
from data.fetcher import StockDataFetcher
import traceback

import tqdm

# class StockSelector:
#     @staticmethod
#     def _calculate_ma(data, window):
#         """计算移动平均线(内部方法)"""
#         return data['close'].rolling(window=window).mean()

#     @staticmethod
#     def find_golden_cross(stock_data):
#         """
#         筛选出现金叉的股票
#         参数:
#             stock_data: DataFrame, 包含日期、收盘价等
#         返回:
#             出现金叉的股票数据
#         """
#         stock_data['ma5'] = StockSelector._calculate_ma(stock_data, 5)
#         stock_data['ma10'] = StockSelector._calculate_ma(stock_data, 10)
        
#         golden_cross = (
#             (stock_data['ma5'] > stock_data['ma10']) & 
#             (stock_data['ma5'].shift(1) <= stock_data['ma10'].shift(1))
#         )
#         return stock_data[golden_cross]

#     @staticmethod
#     def get_golden_cross_stocks(date=None):
#         """
#         获取所有出现金叉的股票
#         参数:
#             date: 指定日期(格式: 'YYYYMMDD'), 默认为None表示最新数据
#         返回:
#             出现金叉的股票列表(代码, 名称)
#         """
#         all_stocks = StockDataFetcher.get_all_stocks()
#         golden_cross_stocks = []
        
#         for code, name in tqdm.tqdm(all_stocks):
#             try:
#                 fetcher = StockDataFetcher(code)
#                 data = fetcher.get_historical_data(
#                     start_date=(datetime.now() - pd.Timedelta(days=30)).strftime('%Y%m%d'),
#                     end_date=date if date else datetime.now().strftime('%Y%m%d')
#                 )
                
#                 if len(data) >= 20:
#                     result = StockSelector.find_golden_cross(data)
#                     if not result.empty and result.index[-1].strftime('%Y%m%d') == (date if date else datetime.now().strftime('%Y%m%d')):
#                         golden_cross_stocks.append((code, name))
#             except Exception as e:
#                 print(f"处理股票 {code} 时出错: {e}")
#                 continue
                
#         return golden_cross_stocks
    
#     # from data.selector import StockSelector


# if __name__ == "__main__":
#     # 获取当天金叉股票
#     golden_stocks = StockSelector.get_golden_cross_stocks()
#     print(golden_stocks)


import backtrader as bt

# 定义策略
class GoldenCrossStrategy(bt.Strategy):
    def __init__(self):
        # 为每个股票数据创建均线和交叉信号
        self.crossovers = {}
        self.golden_cross_stocks = []
        for data in self.datas:
            # 计算均线（示例：5日均线和20日均线）
            short_ma = bt.ind.SMA(data.close, period=5)
            long_ma = bt.ind.SMA(data.close, period=10)
            # 记录金叉信号（短期上穿长期）
            self.crossovers[data._name] = bt.ind.CrossOver(short_ma, long_ma)

    def next(self):
        # 在每日收盘后检查信号
        current_date = self.datas[0].datetime.date(0)  # 获取当前日期
        for data in self.datas:
            # 如果当日金叉信号为1（上穿）
            if self.crossovers[data._name][0] == 1:
                print(f"[{current_date}] 股票 {data._name} 出现金叉")
                self.golden_cross_stocks.append({
                    "date": current_date,
                    "code": data.code,
                    "name": data._name
                })
# 添加一个函数将DataFrame转换为backtrader数据格式
def create_backtrader_data(df, name, code):
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # 如果索引是日期，设为None会自动识别
        # open=0,         # 列索引或列名
        # high=1,         # 列索引或列名
        # low=2,          # 列索引或列名
        # close=3,        # 列索引或列名
        # volume=4,       # 列索引或列名
        # openinterest=-1, # 如果没有持仓量数据，设为-1
        # preload=True,  # 强制预加载
        # lazy=False
    )
    data._name = name
    data.code = code
    return data

def run_screen(date=None):
    cerebro = bt.Cerebro()
    # 添加多个股票数据
    all_stocks = StockDataFetcher.get_all_stocks()[100:]
    for code, name in tqdm.tqdm(all_stocks):
        try:
            fetcher = StockDataFetcher(code)
            data = fetcher.get_historical_data(
                start_date=(datetime.now() - pd.Timedelta(days=50)).strftime('%Y%m%d'),
                end_date=date if date else datetime.now().strftime('%Y%m%d')
            )
            if (not isinstance(data, pd.DataFrame)) or len(data) < 15:
                print(f"跳过 {name}：数据不足15天")
                continue
            if not data.empty:
                bt_data = create_backtrader_data(data, name, code)
                cerebro.adddata(bt_data)
        except Exception as e:
            print(f"处理股票 {code} 时出错: {e}")
            print(traceback.format_exc())
    # 添加策略
    cerebro.addstrategy(GoldenCrossStrategy)
    # 运行回测（不涉及资金管理）
    strategies = cerebro.run(stdstats=False)
    return strategies[0].golden_cross_stocks

if __name__ == '__main__':
    result = run_screen()
    for item in result:
        print(f"日期: {item['date']}, 代码: {item['code']}, 名称: {item['name']}")