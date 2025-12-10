# 전략 개발 가이드

## 📋 개요

이 문서는 새로운 트레이딩 전략을 개발하는 방법을 설명합니다.

## 🏗️ 전략 구조

### 베이스 클래스

모든 전략은 `BaseStrategy`를 상속받아 구현합니다.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

class BaseStrategy(ABC):
    """전략 베이스 클래스"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
        self.positions: Dict[str, float] = {}
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        시그널 생성
        
        Returns:
            {
                'action': 'BUY' | 'SELL' | 'HOLD',
                'symbol': str,
                'quantity': float,
                'price': float,
                'reason': str
            }
        """
        pass
    
    @abstractmethod
    def validate_params(self) -> bool:
        """파라미터 검증"""
        pass
    
    def on_order_filled(self, order: Dict[str, Any]) -> None:
        """주문 체결 콜백"""
        pass
    
    def on_error(self, error: Exception) -> None:
        """에러 핸들링"""
        pass
```

## 📊 전략 유형별 가이드

### 1. 김프 차익거래 (Phase 1)

```python
class KimpCashCarryStrategy(BaseStrategy):
    """
    김프 차익거래 전략
    - 롱: 업비트 BTC 현물
    - 숏: 바이낸스 BTCUSDT 무기한 선물
    """
    
    def __init__(self, params: Dict[str, Any]):
        super().__init__('kimp_cash_carry', params)
        self.entry_threshold = params.get('entry_threshold', 0.03)  # 3%
        self.exit_threshold = params.get('exit_threshold', 0.01)    # 1%
        
    def calculate_kimp(self, upbit_price: float, binance_price: float, usd_krw: float) -> float:
        """김프율 계산"""
        binance_krw = binance_price * usd_krw
        return (upbit_price - binance_krw) / binance_krw
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        # 구현 예정
        pass
```

### 2. 추세 추종 (Phase 2)

- Moving Average Crossover
- Breakout Strategy
- Momentum Strategy

### 3. 평균 회귀 (Phase 3)

- Bollinger Bands
- RSI Mean Reversion
- Pairs Trading

### 4. 머신러닝 (Phase 4)

- LSTM 가격 예측
- XGBoost 방향 분류
- Reinforcement Learning

## ⚠️ 주의사항

### Look-ahead Bias 방지

```python
# ❌ 잘못된 예 - 미래 데이터 사용
signal = data['close'].shift(-1) > data['close']  # shift(-1)은 미래 데이터

# ✅ 올바른 예 - 과거 데이터만 사용
signal = data['close'].shift(1) < data['close']   # shift(1)은 과거 데이터
```

### 과최적화 방지

- Walk-Forward 검증 사용
- Out-of-Sample 테스트 필수
- 파라미터 수 최소화

## 🧪 테스트 가이드

```python
import pytest
from src.strategies.kimp.cash_carry import KimpCashCarryStrategy

def test_kimp_calculation():
    strategy = KimpCashCarryStrategy({'entry_threshold': 0.03})
    
    # 업비트: 1억 3천, 바이낸스: $100,000, 환율: 1,300원
    kimp = strategy.calculate_kimp(
        upbit_price=130_000_000,
        binance_price=100_000,
        usd_krw=1_300
    )
    
    assert kimp == 0.0  # 김프 0%
```

## 📁 파일 구조

새 전략 추가 시:

```
src/strategies/
├── base.py                 # 베이스 클래스 (수정 X)
├── kimp/                   # 김프 전략
│   ├── __init__.py
│   └── cash_carry.py
└── trend/                  # 추세 전략 (새로 추가)
    ├── __init__.py
    ├── ma_crossover.py
    └── breakout.py
```
