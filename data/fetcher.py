import akshare as ak
import pandas as pd
from datetime import datetime

class StockDataFetcher:
    def __init__(self, symbol):
        self.symbol = symbol

    def get_historical_data(self, frequency='daily', start_date=None, end_date=None, adjust=""):
        if start_date:
            start_date = datetime.strptime(start_date, '%Y%m%d').strftime('%Y%m%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y%m%d').strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=self.symbol,
            period=frequency,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        df = df.rename(columns={
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '日期': 'date'
        })
        
        df.index = pd.to_datetime(df.date)
        df["openinterest"] = 0
        return df[["open", "high", "low", "close", "volume", "openinterest"]]

    @staticmethod
    def get_all_stocks():
        df = ak.stock_zh_a_spot_em()
        filtered_df = df[
            (~df['代码'].str.startswith('8')) &
            (~df['代码'].str.startswith('688')) &
            (~df['代码'].str.startswith('300')) &
            (~df['名称'].str.contains('ST')) &
            (~df['名称'].str.contains('退')) &
            (~df['名称'].str.contains('风险'))
        ]
        return filtered_df[['代码', '名称']].values.tolist()
