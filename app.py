"""
Modern Portfolio Theory Optimizer - Flask Backend
Advanced portfolio optimization with multiple strategies and risk analysis
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import json
import sqlite3
from io import BytesIO
import base64

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend suitable for server rendering
import matplotlib.pyplot as plt
import yfinance as yf

app = Flask(__name__)
CORS(app)

# Database initialization
def init_db():
    """Initialize SQLite database for storing portfolio history"""
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optimizations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  tickers TEXT,
                  strategy TEXT,
                  optimal_weights TEXT,
                  expected_return REAL,
                  volatility REAL,
                  sharpe_ratio REAL,
                  risk_free_rate REAL)''')
    conn.commit()
    conn.close()

init_db()

# Default ticker universe for UI suggestions (prices are fetched on-demand via yfinance)
DEFAULT_TICKERS: List[str] = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'JPM', 'V', 'META', 'NFLX',
    'DIS', 'BAC', 'XOM', 'JNJ', 'PG', 'KO', 'PEP', 'UNH', 'ADBE', 'HD'
]

# Simple in-memory cache for price history to reduce repeated external requests
PRICE_CACHE: Dict[Tuple[Tuple[str, ...], str, str], Dict[str, Any]] = {}
PRICE_CACHE_TTL = timedelta(minutes=30)


def _download_price_history(tickers: List[str], period: str, interval: str) -> pd.DataFrame:
    """Fetch adjusted close prices for the given tickers from yfinance."""
    if not tickers:
        raise ValueError('No tickers provided')

    normalized_tickers = [ticker.upper().strip() for ticker in tickers if ticker]
    if len(normalized_tickers) < 2:
        raise ValueError('Need at least 2 tickers for analysis')

    raw_data = yf.download(
        tickers=' '.join(normalized_tickers),
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by='ticker'
    )

    if raw_data.empty:
        raise ValueError('No price data retrieved from yfinance for the provided tickers')

    if isinstance(raw_data.columns, pd.MultiIndex):
        level_names = raw_data.columns.get_level_values(1)
        if 'Adj Close' in level_names:
            prices_df = raw_data.xs('Adj Close', axis=1, level=1)
        elif 'Close' in level_names:
            prices_df = raw_data.xs('Close', axis=1, level=1)
        else:
            raise ValueError('Unable to locate closing prices in yfinance response')
        prices_df.columns = [str(col).upper() for col in prices_df.columns]
    else:
        if 'Adj Close' in raw_data.columns:
            prices_df = raw_data[['Adj Close']].copy()
        elif 'Close' in raw_data.columns:
            prices_df = raw_data[['Close']].copy()
        else:
            raise ValueError('Unable to locate closing prices in yfinance response')
        prices_df.columns = [normalized_tickers[0]]

    prices_df.index = pd.to_datetime(prices_df.index)
    prices_df = prices_df.sort_index()
    prices_df = prices_df.loc[~prices_df.index.duplicated(keep='last')]

    available_columns = [ticker for ticker in normalized_tickers if ticker in prices_df.columns]
    if len(available_columns) < 2:
        raise ValueError('At least two tickers must have price history over the selected period')

    prices_df = prices_df[available_columns]
    prices_df = prices_df.dropna(how='any')

    if prices_df.empty or len(prices_df) < 2:
        raise ValueError('Not enough overlapping price data for the selected tickers')

    return prices_df


def _get_price_history(tickers: List[str], period: str, interval: str) -> pd.DataFrame:
    cache_key = (tuple(sorted(tickers)), period, interval)
    now = datetime.utcnow()
    cached_entry = PRICE_CACHE.get(cache_key)

    if cached_entry:
        cached_timestamp = cached_entry['timestamp']
        if now - cached_timestamp < PRICE_CACHE_TTL:
            return cached_entry['data'].copy(deep=True)

    prices_df = _download_price_history(tickers, period, interval)
    PRICE_CACHE[cache_key] = {
        'timestamp': now,
        'data': prices_df.copy(deep=True)
    }
    return prices_df.copy(deep=True)

class PortfolioOptimizer:
    """Advanced portfolio optimizer with multiple strategies"""

    def __init__(self, tickers, risk_free_rate=0.02, price_period='5y', price_interval='1d'):
        self.tickers = [ticker.upper().strip() for ticker in tickers if ticker]
        self.risk_free_rate = risk_free_rate
        self.price_period = price_period
        self.price_interval = price_interval
        self.price_history: pd.DataFrame | None = None
        self.returns_df: pd.DataFrame | None = None
        self.mean_returns: pd.Series | None = None
        self.cov_matrix: pd.DataFrame | None = None
        
    def load_data(self):
        """Load and process price data"""
        try:
            if len(self.tickers) < 2:
                raise ValueError('Need at least 2 tickers for analysis')

            prices_df = _get_price_history(self.tickers, self.price_period, self.price_interval)

            self.price_history = prices_df
            self.tickers = list(prices_df.columns)

            self.returns_df = np.log(prices_df / prices_df.shift(1)).dropna()
            if self.returns_df.empty:
                raise ValueError('Not enough price history to compute returns')

            self.mean_returns = self.returns_df.mean() * 252
            self.cov_matrix = self.returns_df.cov() * 252

            return True
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def portfolio_stats(self, weights):
        """Calculate portfolio statistics"""
        weights = np.array(weights)
        returns = np.sum(self.mean_returns * weights)
        volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe = (returns - self.risk_free_rate) / volatility
        return returns, volatility, sharpe
    
    def monte_carlo_simulation(self, num_portfolios=10000):
        """Run Monte Carlo simulation"""
        results = np.zeros((4, num_portfolios))
        weights_record = []
        
        for i in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(len(self.tickers))
            weights /= np.sum(weights)
            weights_record.append(weights)
            
            # Calculate portfolio stats
            returns, volatility, sharpe = self.portfolio_stats(weights)
            
            results[0, i] = returns
            results[1, i] = volatility
            results[2, i] = sharpe
            results[3, i] = i
        
        return results, weights_record
    
    def optimize_sharpe(self):
        """Optimize for maximum Sharpe ratio using scipy"""
        num_assets = len(self.tickers)
        
        def neg_sharpe(weights):
            _, _, sharpe = self.portfolio_stats(weights)
            return -sharpe
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(neg_sharpe, initial_guess, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def optimize_min_volatility(self):
        """Optimize for minimum volatility"""
        num_assets = len(self.tickers)
        
        def portfolio_volatility(weights):
            _, volatility, _ = self.portfolio_stats(weights)
            return volatility
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(portfolio_volatility, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def optimize_target_return(self, target_return):
        """Optimize for minimum volatility given target return"""
        num_assets = len(self.tickers)
        
        def portfolio_volatility(weights):
            _, volatility, _ = self.portfolio_stats(weights)
            return volatility
        
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
        )
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(portfolio_volatility, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x if result.success else None
    
    def efficient_frontier(self, num_points=100):
        """Generate efficient frontier curve"""
        min_return = self.mean_returns.min()
        max_return = self.mean_returns.max()
        target_returns = np.linspace(min_return, max_return, num_points)
        
        efficient_portfolios = []
        for target in target_returns:
            weights = self.optimize_target_return(target)
            if weights is not None:
                returns, volatility, sharpe = self.portfolio_stats(weights)
                efficient_portfolios.append({
                    'return': returns,
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'weights': weights.tolist()
                })
        
        return efficient_portfolios

    def render_portfolio_chart(self, mc_results, frontier=None, optimal=None,
                               risk_free_rate=None, num_portfolios=None):
        """Render efficient frontier and Monte Carlo scatter plot using matplotlib"""
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Monte Carlo scatter colored by Sharpe ratio
        scatter = ax.scatter(
            mc_results[1],
            mc_results[0],
            c=mc_results[2],
            cmap='viridis',
            s=12,
            alpha=0.45,
            edgecolor='none',
            label='Monte Carlo Portfolios'
        )

        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label('Sharpe Ratio', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

        # Efficient frontier curve
        if frontier:
            frontier_vol = [point['volatility'] for point in frontier]
            frontier_ret = [point['return'] for point in frontier]
            ax.plot(frontier_vol, frontier_ret, color='#ffb454', linewidth=2.5, label='Efficient Frontier')

        # Optimal portfolio point
        if optimal:
            ax.scatter(
                optimal['volatility'],
                optimal['return'],
                color='#ff4d4f',
                marker='*',
                s=320,
                label='Optimal Portfolio'
            )

        title_parts = ['Efficient Frontier & Portfolio Scatter']
        if risk_free_rate is not None:
            title_parts.append(f"Risk-Free: {risk_free_rate * 100:.2f}%")
        if num_portfolios is not None:
            title_parts.append(f"Simulations: {num_portfolios:,}")
        ax.set_title(' | '.join(title_parts), color='white', fontsize=14, pad=16)
        ax.set_xlabel('Volatility (Std. Dev)', color='white')
        ax.set_ylabel('Expected Return', color='white')
        ax.tick_params(axis='both', colors='white')
        ax.grid(color='white', alpha=0.1)
        legend = ax.legend(facecolor='#1f2937', edgecolor='none', framealpha=0.8, labelcolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def render_correlation_heatmap(self):
        """Render correlation heatmap for selected assets"""
        if self.returns_df is None:
            raise ValueError('Returns data not loaded')

        corr = self.returns_df.corr()
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 6))

        cax = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
        fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label='Correlation')

        tick_labels = corr.columns
        ax.set_xticks(range(len(tick_labels)))
        ax.set_yticks(range(len(tick_labels)))
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
        ax.set_yticklabels(tick_labels, color='white')

        ax.set_title('Asset Correlation Heatmap', color='white', fontsize=14, pad=16)
        ax.grid(False)

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

# API Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/tickers', methods=['GET'])
def get_available_tickers():
    """Get list of available tickers"""
    return jsonify({
        'success': True,
        'tickers': DEFAULT_TICKERS
    })

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio():
    """Optimize portfolio using specified strategy"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        strategy = data.get('strategy', 'max_sharpe')
        risk_free_rate = data.get('risk_free_rate', 0.02)
        num_simulations = data.get('num_simulations', 10000)
        price_period = data.get('period', '5y')
        price_interval = data.get('interval', '1d')
        
        if len(tickers) < 2:
            return jsonify({'success': False, 'error': 'Need at least 2 tickers'}), 400
        
        # Initialize optimizer
        optimizer = PortfolioOptimizer(tickers, risk_free_rate, price_period=price_period, price_interval=price_interval)
        optimizer.load_data()

        # Run Monte Carlo simulation and efficient frontier
        mc_results, mc_weights = optimizer.monte_carlo_simulation(num_simulations)
        frontier = optimizer.efficient_frontier(100)
        
        # Get optimal portfolio based on strategy
        if strategy == 'max_sharpe':
            optimal_weights = optimizer.optimize_sharpe()
        elif strategy == 'min_volatility':
            optimal_weights = optimizer.optimize_min_volatility()
        elif strategy == 'monte_carlo':
            # Use best from Monte Carlo
            max_sharpe_idx = np.argmax(mc_results[2])
            optimal_weights = mc_weights[max_sharpe_idx]
        else:
            return jsonify({'success': False, 'error': 'Invalid strategy'}), 400
        
        # Calculate optimal portfolio stats
        opt_return, opt_volatility, opt_sharpe = optimizer.portfolio_stats(optimal_weights)

        optimal_summary = {
            'weights': {ticker: float(weight) for ticker, weight in zip(optimizer.tickers, optimal_weights)},
            'return': float(opt_return),
            'volatility': float(opt_volatility),
            'sharpe': float(opt_sharpe)
        }

        # Render backend chart image
        chart_image = optimizer.render_portfolio_chart(
            mc_results,
            frontier=frontier,
            optimal=optimal_summary,
            risk_free_rate=risk_free_rate,
            num_portfolios=num_simulations
        )
        
        # Save to database
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute('''INSERT INTO optimizations 
                     (timestamp, tickers, strategy, optimal_weights, expected_return, 
                      volatility, sharpe_ratio, risk_free_rate)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), ','.join(optimizer.tickers), strategy,
                   json.dumps(optimal_weights.tolist()), float(opt_return), 
                   float(opt_volatility), float(opt_sharpe), risk_free_rate))
        conn.commit()
        optimization_id = c.lastrowid
        conn.close()
        
        # Prepare response
        response = {
            'success': True,
            'optimization_id': optimization_id,
            'optimal': optimal_summary,
            'monte_carlo': {
                'returns': mc_results[0].tolist(),
                'volatilities': mc_results[1].tolist(),
                'sharpes': mc_results[2].tolist()
            },
            'tickers': optimizer.tickers,
            'strategy': strategy,
            'frontier': frontier,
            'chart_image': chart_image
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/efficient-frontier', methods=['POST'])
def get_efficient_frontier():
    """Calculate efficient frontier"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        risk_free_rate = data.get('risk_free_rate', 0.02)
        num_points = data.get('num_points', 50)
        price_period = data.get('period', '5y')
        price_interval = data.get('interval', '1d')

        optimizer = PortfolioOptimizer(
            tickers,
            risk_free_rate,
            price_period=price_period,
            price_interval=price_interval
        )
        optimizer.load_data()
        
        frontier = optimizer.efficient_frontier(num_points)
        
        return jsonify({
            'success': True,
            'frontier': frontier,
            'tickers': optimizer.tickers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio-stats', methods=['POST'])
def calculate_portfolio_stats():
    """Calculate statistics for custom weights"""
    try:
        data = request.json
        tickers = data.get('tickers', [])
        weights = data.get('weights', [])
        risk_free_rate = data.get('risk_free_rate', 0.02)
        price_period = data.get('period', '5y')
        price_interval = data.get('interval', '1d')
        
        if len(tickers) != len(weights):
            return jsonify({'success': False, 'error': 'Tickers and weights length mismatch'}), 400
        
        if abs(sum(weights) - 1.0) > 0.01:
            return jsonify({'success': False, 'error': 'Weights must sum to 1'}), 400
        
        optimizer = PortfolioOptimizer(
            tickers,
            risk_free_rate,
            price_period=price_period,
            price_interval=price_interval
        )
        optimizer.load_data()
        
        returns, volatility, sharpe = optimizer.portfolio_stats(weights)
        
        return jsonify({
            'success': True,
            'return': float(returns),
            'volatility': float(volatility),
            'sharpe': float(sharpe)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_optimization_history():
    """Get optimization history from database"""
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute('''SELECT id, timestamp, tickers, strategy, optimal_weights, 
                     expected_return, volatility, sharpe_ratio 
                     FROM optimizations 
                     ORDER BY timestamp DESC 
                     LIMIT 50''')
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'timestamp': row[1],
                'tickers': row[2].split(','),
                'strategy': row[3],
                'optimal_weights': json.loads(row[4]),
                'expected_return': row[5],
                'volatility': row[6],
                'sharpe_ratio': row[7]
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/correlation', methods=['POST'])
def get_correlation_matrix():
    """Get correlation matrix for selected tickers"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        price_period = data.get('period', '5y')
        price_interval = data.get('interval', '1d')

        optimizer = PortfolioOptimizer(
            tickers,
            price_period=price_period,
            price_interval=price_interval
        )
        optimizer.load_data()
        
        correlation = optimizer.returns_df.corr()
        heatmap_image = optimizer.render_correlation_heatmap()
        
        return jsonify({
            'success': True,
            'correlation': correlation.to_dict(),
            'tickers': optimizer.tickers,
            'chart_image': heatmap_image
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Modern Portfolio Theory Optimizer Server")
    print("📊 Suggested tickers:", ', '.join(DEFAULT_TICKERS))
    print("🌐 Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
