# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Taiwan stock market analysis and trading strategy repository that combines R and Python for data collection, analysis, and strategy backtesting. The project focuses on Taiwan Stock Exchange (TWSE) listed companies and uses technical indicators for trading signal generation.

## Architecture

### Data Flow
1. **Data Collection (R)**: `Stock_crawler.R` fetches Taiwan stock data from FinMind API
2. **Data Storage**: Raw daily data stored in `日線/` directory, processed monthly data in `月線/` directory  
3. **Analysis (Python)**: `main.py` performs technical analysis and generates trading signals
4. **Output**: Trading charts and performance metrics

### Key Components

**Stock_crawler.R**:
- Connects to FinMind API using hardcoded credentials (user_id: "Ikjoy1004")
- Functions: `GetStockInfo()`, `CalMonthData()`, `main()`, `main2()`
- Processes Taiwan stock list from `台股上市櫃普通股.csv`
- Outputs JSON files for daily (`日線/`) and monthly (`月線/`) data

**main.py**: 
- Technical analysis using RSI, Bollinger Bands, and Fibonacci retracements
- Trading strategy with stop-loss mechanism (20% default)
- Functions: `compute_rsi()`, `fibonacci_levels()`, `generate_signals()`, `calculate_returns()`
- Generates comprehensive trading charts and performance comparison

## Common Commands

### Running the Analysis
```bash
# Install Python dependencies
pip install -r stock-analysis-requirements.txt

# Run the main trading strategy analysis  
python main.py

# For R data collection (requires R environment)
Rscript Stock_crawler.R
```

### Data Structure
- `日線/`: Daily stock data in JSON format (e.g., `2330.json` for TSMC)
- `月線/`: Monthly aggregated data (e.g., `2330_month.json`)
- Stock codes follow Taiwan stock market format (4-digit numbers)

## Dependencies

**Python** (stock-analysis-requirements.txt):
- pandas, numpy, matplotlib for data analysis and visualization
- Scientific computing: scikit-learn, statsmodels

**R**:
- jsonlite, dplyr, lubridate for data processing
- httr for API requests
- ggplot2 for visualization

## Important Notes

- The R script contains hardcoded API credentials that should be externalized
- Default analysis in main.py uses stock 6257 from `日線/6257.json`
- Trading strategy uses 20% stop-loss with RSI<35 buy signals and various sell conditions
- All stock data follows Taiwan market timezone and trading calendar