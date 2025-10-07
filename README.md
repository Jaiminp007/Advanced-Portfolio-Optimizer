# Advanced Modern Portfolio Theory Optimizer

A sophisticated full-stack web application for portfolio optimization using Modern Portfolio Theory (MPT) with Python Flask backend and interactive frontend.

## 🚀 Features

### Advanced Portfolio Optimization
- **Multiple Optimization Strategies:**
  - Maximum Sharpe Ratio optimization using SciPy
  - Minimum Volatility optimization
  - Monte Carlo simulation with 10,000+ portfolios
  
### Interactive Visualizations
- **Efficient Frontier Chart** - Visualize the risk-return tradeoff
- **Monte Carlo Scatter Plot** - See all simulated portfolios
- **Correlation Heatmap** - Understand asset relationships
- **Portfolio Weight Charts** - Pie and bar charts for allocation

### Advanced Analytics
- **Risk Metrics Dashboard** - VaR, Diversification Score, Max Position
- **Portfolio Comparison** - Compare multiple strategies side-by-side
- **Optimization History** - SQLite database tracking all optimizations
- **Real-time Calculations** - Powered by NumPy, Pandas, and SciPy

## 📦 Tech Stack

### Backend
- **Flask** - Web framework
- **NumPy** - Numerical computations
- **Pandas** - Data manipulation
- **SciPy** - Optimization algorithms
- **SQLite** - Database for history tracking

### Frontend
- **Tailwind CSS** - Modern styling
- **Plotly.js** - Interactive charts
- **Chart.js** - Additional visualizations
- **Lucide Icons** - Beautiful icons

## 🛠️ Installation

1. **Clone the repository**
```bash
cd /Users/jaiminpatel/github/stock
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🎯 Usage

1. **Start the Flask server**
```bash
python app.py
```

The server will start at `http://localhost:5000`

2. **Open your browser**
Navigate to `http://localhost:5000`

3. **Optimize your portfolio**
   - Enter stock tickers (comma-separated): `AAPL, MSFT, GOOG, AMZN, TSLA`
   - Choose optimization strategy
   - Click "Optimize Portfolio"
   - View results, charts, and analytics

## 📊 Available Stock Tickers

Historical prices are fetched on-demand from Yahoo Finance via [`yfinance`](https://pypi.org/project/yfinance/). The dashboard suggests a curated starter list, but you can request any symbols supported by Yahoo Finance:
- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation
- **GOOGL** - Alphabet Inc.
- **AMZN** - Amazon.com Inc.
- **TSLA** - Tesla Inc.
- **NVDA** - NVIDIA Corporation
- **JPM** - JPMorgan Chase & Co.
- **V** - Visa Inc.
- **META** - Meta Platforms Inc.
- **NFLX** - Netflix Inc.

> 💡 Tip: mix in ETFs (e.g., `SPY`, `QQQ`) or sector funds to explore diversified allocations.

## 🔧 API Endpoints

### Portfolio Optimization
```
POST /api/optimize
Body: {
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "strategy": "max_sharpe",
  "risk_free_rate": 0.02,
  "num_simulations": 10000
}
```

### Efficient Frontier
```
POST /api/efficient-frontier
Body: {
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "risk_free_rate": 0.02,
  "num_points": 50
}
```

### Correlation Matrix
```
POST /api/correlation
Body: {
  "tickers": ["AAPL", "MSFT", "GOOG"]
}
```

### Portfolio Statistics
```
POST /api/portfolio-stats
Body: {
  "tickers": ["AAPL", "MSFT", "GOOG"],
  "weights": [0.33, 0.33, 0.34],
  "risk_free_rate": 0.02
}
```

### Optimization History
```
GET /api/history
```

### Available Tickers
```
GET /api/tickers
```

## 📈 How It Works

### 1. Data Processing
- Downloads up to five years of adjusted closing prices via yfinance (configurable per request)
- Calculates logarithmic daily returns
- Computes annualized mean returns and covariance matrix

### 2. Monte Carlo Simulation
- Generates 10,000+ random portfolio weight combinations
- Calculates return, volatility, and Sharpe ratio for each
- Identifies the optimal portfolio

### 3. Optimization Algorithms
- **Max Sharpe:** Uses SciPy's SLSQP optimizer to maximize Sharpe ratio
- **Min Volatility:** Minimizes portfolio standard deviation
- **Monte Carlo:** Selects best portfolio from simulation

### 4. Efficient Frontier
- Generates optimal portfolios for various target returns
- Visualizes the risk-return tradeoff curve

## 🎨 Features Breakdown

### Main Dashboard
- Input section with validation
- Multiple optimization strategies
- Adjustable risk-free rate and simulation count
- Real-time error handling and notifications

### Results Display
- Key metrics cards (Return, Volatility, Sharpe Ratio)
- Optimal weight allocation with visual bars
- Interactive efficient frontier chart
- Pie chart for weight distribution

### Advanced Tabs
1. **Optimizer** - Main optimization interface
2. **Portfolio Comparison** - Compare strategies
3. **Risk Analytics** - Detailed risk metrics
4. **Correlation Matrix** - Asset correlation heatmap

### Error Handling
- Comprehensive try-catch blocks throughout
- Validation for all user inputs
- Null reference checks on all data
- Informative error messages
- Connection status monitoring

## 🔐 Database Schema

```sql
CREATE TABLE optimizations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT,
  tickers TEXT,
  strategy TEXT,
  optimal_weights TEXT,
  expected_return REAL,
  volatility REAL,
  sharpe_ratio REAL,
  risk_free_rate REAL
)
```

## 🐛 Troubleshooting

### "Cannot connect to server" error
- Make sure Flask is running: `python app.py`
- Check if port 5000 is available
- Verify firewall settings

### "Cannot read properties of null" error
**FIXED!** The application now includes:
- Comprehensive null checks on all data
- Validation before accessing properties
- Proper error boundaries
- Fallback values for missing data

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

## 📝 License

This project is for educational purposes and demonstrates Modern Portfolio Theory concepts.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📚 Learn More

- [Modern Portfolio Theory](https://en.wikipedia.org/wiki/Modern_portfolio_theory)
- [Sharpe Ratio](https://en.wikipedia.org/wiki/Sharpe_ratio)
- [Efficient Frontier](https://en.wikipedia.org/wiki/Efficient_frontier)
- [Monte Carlo Simulation](https://en.wikipedia.org/wiki/Monte_Carlo_method)

---

Built with ❤️ using Flask, NumPy, Pandas, SciPy, and Modern Web Technologies
