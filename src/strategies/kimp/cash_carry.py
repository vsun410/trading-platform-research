"""김프 차익거래 (Cash & Carry Arbitrage) 전략

전략 개요:
- 롱: 업비트 BTC 현물 매수
- 숏: 바이낸스 BTCUSDT 무기한 선물 매도
- 수익원: 김프(프리미엄) + 펀딩비

진입 조건:
- 김프율이 entry_threshold 이상일 때

청산 조건:
- 김프율이 exit_threshold 이하일 때
"""

from typing import Dict, Any, Optional
import pandas as pd

from ..base import BaseStrategy, Signal


class KimpCashCarryStrategy(BaseStrategy):
    """
    김프 차익거래 전략
    
    Args:
        params: {
            'entry_threshold': float,  # 진입 김프율 (기본: 0.03 = 3%)
            'exit_threshold': float,   # 청산 김프율 (기본: 0.01 = 1%)
            'position_size': float,    # 포지션 크기 비율 (기본: 1.0 = 100%)
        }
    
    Example:
        >>> strategy = KimpCashCarryStrategy({
        ...     'entry_threshold': 0.03,
        ...     'exit_threshold': 0.01
        ... })
        >>> signal = strategy.generate_signal(data)
    """
    
    def __init__(self, params: Dict[str, Any]):
        # 기본값 설정
        default_params = {
            'entry_threshold': 0.03,   # 3%
            'exit_threshold': 0.01,    # 1%
            'position_size': 1.0,      # 100%
        }
        merged_params = {**default_params, **params}
        super().__init__('kimp_cash_carry', merged_params)
        
        self.entry_threshold = self.params['entry_threshold']
        self.exit_threshold = self.params['exit_threshold']
        self.position_size = self.params['position_size']
        
        # 상태
        self.is_in_position = False
    
    def validate_params(self) -> bool:
        """파라미터 검증"""
        if self.params.get('entry_threshold', 0) <= 0:
            return False
        if self.params.get('exit_threshold', 0) < 0:
            return False
        if self.params.get('entry_threshold', 0) <= self.params.get('exit_threshold', 0):
            return False
        if not 0 < self.params.get('position_size', 0) <= 1:
            return False
        return True
    
    def calculate_kimp(
        self, 
        upbit_price: float, 
        binance_price: float, 
        usd_krw: float
    ) -> float:
        """
        김프율 계산
        
        Args:
            upbit_price: 업비트 가격 (KRW)
            binance_price: 바이낸스 가격 (USDT)
            usd_krw: USD/KRW 환율
            
        Returns:
            김프율 (예: 0.03 = 3%)
        """
        binance_krw = binance_price * usd_krw
        if binance_krw == 0:
            return 0
        return (upbit_price - binance_krw) / binance_krw
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[Signal]:
        """
        시그널 생성
        
        Args:
            data: DataFrame with columns:
                - timestamp
                - upbit_price (KRW)
                - binance_price (USDT)
                - usd_krw (환율)
                
        Returns:
            Signal 또는 None
        """
        if data.empty:
            return None
            
        # 최신 데이터
        latest = data.iloc[-1]
        timestamp = latest.get('timestamp')
        upbit_price = latest.get('upbit_price', 0)
        binance_price = latest.get('binance_price', 0)
        usd_krw = latest.get('usd_krw', 1300)  # 기본 환율
        
        # 김프율 계산
        kimp = self.calculate_kimp(upbit_price, binance_price, usd_krw)
        
        # 포지션 없음 → 진입 조건 확인
        if not self.is_in_position:
            if kimp >= self.entry_threshold:
                self.is_in_position = True
                return Signal(
                    timestamp=timestamp,
                    action='BUY',
                    symbol='BTC',
                    exchange='upbit,binance',
                    quantity=self.position_size,
                    price=upbit_price,
                    reason=f'김프 진입: {kimp:.2%} >= {self.entry_threshold:.2%}',
                    metadata={
                        'kimp': kimp,
                        'upbit_price': upbit_price,
                        'binance_price': binance_price,
                        'usd_krw': usd_krw,
                        'type': 'ENTRY'
                    }
                )
        
        # 포지션 있음 → 청산 조건 확인
        else:
            if kimp <= self.exit_threshold:
                self.is_in_position = False
                return Signal(
                    timestamp=timestamp,
                    action='SELL',
                    symbol='BTC',
                    exchange='upbit,binance',
                    quantity=self.position_size,
                    price=upbit_price,
                    reason=f'김프 청산: {kimp:.2%} <= {self.exit_threshold:.2%}',
                    metadata={
                        'kimp': kimp,
                        'upbit_price': upbit_price,
                        'binance_price': binance_price,
                        'usd_krw': usd_krw,
                        'type': 'EXIT'
                    }
                )
        
        return None
    
    def reset(self) -> None:
        """상태 초기화"""
        super().reset()
        self.is_in_position = False
