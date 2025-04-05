from datetime import datetime
from data.fetcher import StockDataFetcher
from strategies.ma_cross import MA_Cross
from engine.backtester import BacktestEngine
from visualization.plotter import TradeVisualizer

def main():
    fetcher = StockDataFetcher("002031")
    df = fetcher.get_historical_data(
        start_date="20240101",
        end_date="20250404"
    )

    engine = BacktestEngine()
    engine.add_data(df, datetime(2024, 1, 1), datetime(2025, 4, 4))
    engine.add_strategy(MA_Cross)
    engine.add_analyzers()
    
    results = engine.run()
    strat = results[0]
    
    print("最终资产价值: %.2f" % engine.cerebro.broker.getvalue())
    print('累计收益率: %.2f%%' % (strat.analyzers.returns.get_analysis()['rtot']*100))
    
    visualizer = TradeVisualizer()
    visualizer.plot_trades(strat.trades)
    visualizer.plot_drawdown(strat.drawdown_history)
    
    engine.plot_results()

if __name__ == "__main__":
    main()
