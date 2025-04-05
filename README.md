# ai_quantify 项目文档

## 项目概述
ai_quantify 是一个基于 Python 的量化交易项目，目标是借助策略回测和实盘交易达成自动化股票交易。此项目运用 backtrader 库开展回测工作，同时支持多种分析器和可视化工具，用于评估策略表现。

## 项目结构
```
ai_quantify/
├── data/
│   └── fetcher.py          # 数据抓取模块
├── engine/
│   └── backtester.py       # 回测引擎模块
├── strategies/
│   └── ma_cross.py         # 均线交叉策略模块
├── trade_engine.py         # 实盘交易引擎模块
├── main.py                 # 主程序入口
├── visualization/
│   └── plotter.py          # 可视化模块
└── README.md               # 项目说明文档
```

## 安装依赖
要确保已安装以下 Python 库：
```bash
pip install backtrader pandas matplotlib
```

## 运行项目

### 回测模式
```bash
python main.py --mode backtest --ticker 002031 --initial_capital 100000
```

### 实盘交易模式（未实现）
```bash
python main.py --mode trade --ticker 002031 --initial_capital 100000
```

## 策略说明
当前项目实现了如下策略：
- **均线交叉策略 (MA_Cross)**：通过两条移动平均线的交叉来确定买入和卖出时机。

## 模块说明
### 数据抓取
数据抓取模块（`data/fetcher.py`）的作用是从指定数据源获取股票的历史数据。

### 回测引擎
回测引擎模块（`engine/backtester.py`）使用 backtrader 库进行策略回测，并且支持多种分析器和可视化工具，以评估策略表现。

### 实盘交易引擎
实盘交易引擎模块（`trade_engine.py`）负责实盘交易的订单执行和风险管理。

### 可视化
可视化模块（`visualization/plotter.py`）能提供多种图表来展示回测结果，例如 K 线图、回撤图等。

## 日志
回测结果会保存到 `backtest_results.log` 文件中，其中包含初始资金、最终净值、最大回撤、夏普比率、年化收益和交易记录等信息。

## 贡献
欢迎提交问题和改进请求。请按照以下步骤操作：
1. Fork 本仓库。
2. 创建您的功能分支：`git checkout -b feature/AmazingFeature`。
3. 提交您的更改：`git commit -m 'Add some AmazingFeature'`。
4. 推送到分支：`git push origin feature/AmazingFeature`。
5. 打开一个 Pull Request。

## 许可证
本项目采用 MIT 许可证。详情请参阅 `LICENSE` 文件。
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 联系
- **作者**：李国才
- **邮箱**：liguocai@example.com