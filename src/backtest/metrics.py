"""성과 지표 계산"""

from typing import List
import pandas as pd
import numpy as np


class PerformanceMetrics:
    """
    성과 지표 계산기
    
    Args:
        equity_curve: 자산 시계열
        trades: 거래 목록
    """
    
    def __init__(self, equity_curve: pd.Series, trades: List = None):
        self.equity = equity_curve
        self.trades = trades or []
        self.returns = equity_curve.pct_change().dropna()
        
    def total_return(self) -> float:
        """총 수익률"""
        if len(self.equity) < 2:
            return 0.0
        return (self.equity.iloc[-1] - self.equity.iloc[0]) / self.equity.iloc[0]
    
    def cagr(self) -> float:
        """연평균 수익률 (CAGR)"""
        if len(self.equity) < 2:
            return 0.0
        
        total_days = (self.equity.index[-1] - self.equity.index[0]).days
        if total_days <= 0:
            return 0.0
            
        years = total_days / 365
        total_ret = self.total_return()
        
        if total_ret <= -1:
            return -1.0
            
        return (1 + total_ret) ** (1 / years) - 1
    
    def sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        샤프 비율
        
        Args:
            risk_free_rate: 무위험 수익률 (연율, 기본 3%)
            
        Returns:
            연율화된 샤프 비율
        """
        if len(self.returns) < 2:
            return 0.0
            
        excess_returns = self.returns - risk_free_rate / 252
        
        if self.returns.std() == 0:
            return 0.0
            
        return np.sqrt(252) * excess_returns.mean() / self.returns.std()
    
    def max_drawdown(self) -> float:
        """최대 낙폭 (MDD)"""
        if len(self.equity) < 2:
            return 0.0
            
        cummax = self.equity.cummax()
        drawdown = (self.equity - cummax) / cummax
        return abs(drawdown.min())
    
    def win_rate(self) -> float:
        """승률"""
        if not self.trades:
            return 0.0
            
        wins = sum(1 for t in self.trades if t.pnl > 0)
        return wins / len(self.trades)
    
    def profit_factor(self) -> float:
        """Profit Factor (총이익/총손실)"""
        if not self.trades:
            return 0.0
            
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
            
        return gross_profit / gross_loss
    
    def volatility(self, annualize: bool = True) -> float:
        """변동성"""
        if len(self.returns) < 2:
            return 0.0
            
        vol = self.returns.std()
        
        if annualize:
            return vol * np.sqrt(252)
        return vol
    
    def var(self, confidence: float = 0.95) -> float:
        """
        Value at Risk
        
        Args:
            confidence: 신뢰수준 (기본 95%)
            
        Returns:
            일별 VaR
        """
        if len(self.returns) < 2:
            return 0.0
            
        return abs(np.percentile(self.returns, (1 - confidence) * 100))
    
    def summary(self) -> dict:
        """전체 지표 요약"""
        return {
            'total_return': self.total_return(),
            'cagr': self.cagr(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'volatility': self.volatility(),
            'var_95': self.var(0.95),
            'win_rate': self.win_rate(),
            'profit_factor': self.profit_factor(),
            'total_trades': len(self.trades)
        }
