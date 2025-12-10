"""백테스트 엔진"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from ..strategies.base import BaseStrategy, Signal
from .metrics import PerformanceMetrics


@dataclass
class BacktestConfig:
    """백테스트 설정"""
    start_date: str                    # '2023-01-01'
    end_date: str                      # '2024-12-31'
    initial_capital: float = 20_000_000  # 2천만원
    commission_rate: float = 0.001     # 0.1%
    slippage_rate: float = 0.0005      # 0.05%
    

@dataclass
class Trade:
    """거래 기록"""
    timestamp: datetime
    symbol: str
    side: str  # 'BUY', 'SELL'
    quantity: float
    price: float
    commission: float
    pnl: float = 0
    

@dataclass
class BacktestResult:
    """백테스트 결과"""
    config: BacktestConfig
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    
    def summary(self) -> str:
        """결과 요약 문자열"""
        return f"""
========== 백테스트 결과 ==========
기간: {self.config.start_date} ~ {self.config.end_date}
초기 자본: {self.config.initial_capital:,.0f}원

[수익률]
총 수익률: {self.total_return:.2%}
CAGR: {self.cagr:.2%}

[리스크]
Sharpe Ratio: {self.sharpe_ratio:.2f}
Max Drawdown: {self.max_drawdown:.2%}

[거래]
총 거래 수: {self.total_trades}
승률: {self.win_rate:.2%}
Profit Factor: {self.profit_factor:.2f}
=================================
        """


class BacktestEngine:
    """
    벡터화 백테스트 엔진
    
    Example:
        >>> config = BacktestConfig(
        ...     start_date='2023-01-01',
        ...     end_date='2024-12-31',
        ...     initial_capital=20_000_000
        ... )
        >>> engine = BacktestEngine(config)
        >>> result = engine.run(strategy, data)
        >>> print(result.summary())
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        
    def run(self, strategy: BaseStrategy, data: pd.DataFrame) -> BacktestResult:
        """
        백테스트 실행
        
        Args:
            strategy: 전략 객체
            data: OHLCV DataFrame
            
        Returns:
            BacktestResult
        """
        # 초기화
        strategy.reset()
        self.trades = []
        capital = self.config.initial_capital
        self.equity_curve = [capital]
        
        # 데이터 필터링
        mask = (
            (data.index >= self.config.start_date) & 
            (data.index <= self.config.end_date)
        )
        filtered_data = data[mask].copy()
        
        # 시뮬레이션
        for i in range(1, len(filtered_data)):
            # 현재까지의 데이터만 전달 (look-ahead bias 방지)
            current_data = filtered_data.iloc[:i+1]
            
            # 시그널 생성
            signal = strategy.generate_signal(current_data)
            
            if signal:
                # 주문 실행
                trade = self._execute_order(signal, capital)
                if trade:
                    self.trades.append(trade)
                    capital += trade.pnl - trade.commission
            
            self.equity_curve.append(capital)
        
        # 성과 계산
        equity_series = pd.Series(
            self.equity_curve, 
            index=filtered_data.index[:len(self.equity_curve)]
        )
        
        metrics = PerformanceMetrics(equity_series, self.trades)
        
        return BacktestResult(
            config=self.config,
            total_return=metrics.total_return(),
            cagr=metrics.cagr(),
            sharpe_ratio=metrics.sharpe_ratio(),
            max_drawdown=metrics.max_drawdown(),
            win_rate=metrics.win_rate(),
            profit_factor=metrics.profit_factor(),
            total_trades=len(self.trades),
            trades=self.trades,
            equity_curve=equity_series
        )
    
    def _execute_order(
        self, 
        signal: Signal, 
        capital: float
    ) -> Optional[Trade]:
        """
        주문 실행 (시뮬레이션)
        
        Args:
            signal: 시그널
            capital: 현재 자본
            
        Returns:
            Trade 또는 None
        """
        if signal.price is None or signal.price <= 0:
            return None
            
        # 슬리피지 적용
        if signal.action == 'BUY':
            exec_price = signal.price * (1 + self.config.slippage_rate)
        else:
            exec_price = signal.price * (1 - self.config.slippage_rate)
        
        # 수량 계산
        quantity = signal.quantity * capital / exec_price
        
        # 수수료 계산
        commission = quantity * exec_price * self.config.commission_rate
        
        return Trade(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.action,
            quantity=quantity,
            price=exec_price,
            commission=commission,
            pnl=0  # 청산 시 계산
        )
