"""전략 베이스 클래스"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from pydantic import BaseModel


class Signal(BaseModel):
    """트레이딩 시그널"""
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    symbol: str
    exchange: str
    quantity: float
    price: Optional[float] = None
    reason: str = ""
    metadata: Dict[str, Any] = {}


class BaseStrategy(ABC):
    """
    전략 베이스 클래스
    
    모든 전략은 이 클래스를 상속받아 구현합니다.
    
    Example:
        >>> class MyStrategy(BaseStrategy):
        ...     def generate_signal(self, data):
        ...         # 시그널 생성 로직
        ...         pass
    """
    
    def __init__(self, name: str, params: Dict[str, Any]):
        """
        Args:
            name: 전략 이름
            params: 전략 파라미터
        """
        self.name = name
        self.params = params
        self.positions: Dict[str, float] = {}
        self._validate_params()
        
    def _validate_params(self) -> None:
        """파라미터 검증 (내부용)"""
        if not self.validate_params():
            raise ValueError(f"Invalid params for {self.name}: {self.params}")
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Optional[Signal]:
        """
        시그널 생성
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Signal 또는 None (시그널 없음)
        """
        pass
    
    @abstractmethod
    def validate_params(self) -> bool:
        """
        파라미터 검증
        
        Returns:
            유효하면 True
        """
        pass
    
    def on_order_filled(self, order: Dict[str, Any]) -> None:
        """
        주문 체결 콜백
        
        Args:
            order: 체결된 주문 정보
        """
        symbol = order.get('symbol')
        quantity = order.get('quantity', 0)
        side = order.get('side')  # 'BUY' or 'SELL'
        
        if side == 'BUY':
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        elif side == 'SELL':
            self.positions[symbol] = self.positions.get(symbol, 0) - quantity
    
    def on_error(self, error: Exception) -> None:
        """
        에러 핸들링
        
        Args:
            error: 발생한 에러
        """
        pass
    
    def get_position(self, symbol: str) -> float:
        """현재 포지션 조회"""
        return self.positions.get(symbol, 0)
    
    def reset(self) -> None:
        """상태 초기화"""
        self.positions = {}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', params={self.params})"
