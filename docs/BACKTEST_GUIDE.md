# 백테스트 가이드

**Version:** 2.0  
**Date:** 2025-12-12  
**개선사항:** 듀얼 엔진 아키텍처, 고급 슬리피지 모델, Walk-Forward 검증

---

## 📋 개요

전략의 과거 성과를 검증하는 백테스트 시스템입니다. **듀얼 엔진 아키텍처**를 통해 빠른 탐색과 정밀 검증을 모두 지원합니다.

---

## 🏗️ 듀얼 엔진 아키텍처

### 엔진 비교

| 특성 | Vectorized Engine | Event-Driven Engine |
|------|------------------|---------------------|
| **속도** | 🚀 1000x 빠름 | 🐢 느림 |
| **정밀도** | 중간 | 🎯 높음 |
| **호가 반영** | ❌ | ✅ 실제 호가 |
| **슬리피지** | 고정 비율 | 동적 VWAP |
| **용도** | 초기 탐색, 파라미터 그리드 | 최종 검증, 실거래 시뮬레이션 |

### 사용 시나리오

```
┌─────────────────────────────────────────────────────────────────┐
│                    백테스트 워크플로우                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 초기 탐색 (Vectorized)                                     │
│     • 1000개 파라미터 조합 테스트                               │
│     • 소요 시간: ~10분                                          │
│     • 상위 10개 후보 선정                                       │
│                                                                 │
│  2️⃣ 정밀 검증 (Event-Driven)                                   │
│     • 상위 10개 후보만 정밀 테스트                              │
│     • 실제 호가 데이터 사용                                     │
│     • 소요 시간: ~30분                                          │
│                                                                 │
│  3️⃣ Walk-Forward 검증                                          │
│     • 최종 후보 2-3개                                           │
│     • 과적합 검증                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Vectorized Engine (빠른 탐색용)

### 구조

```python
# src/backtest/engines/vectorized_engine.py

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class VectorizedConfig:
    """벡터화 백테스트 설정"""
    initial_capital: float = 20_000_000
    commission_rate: float = 0.001      # 0.1%
    slippage_rate: float = 0.0005       # 0.05% (고정)


class VectorizedEngine:
    """
    벡터화 백테스트 엔진
    
    장점: NumPy 연산으로 1000x 빠름
    단점: 호가 반영 불가, 고정 슬리피지
    용도: 파라미터 그리드 서치, 초기 필터링
    """
    
    def __init__(self, config: VectorizedConfig):
        self.config = config
    
    def run(self, signals: pd.Series, prices: pd.DataFrame) -> Dict[str, Any]:
        """
        벡터화 백테스트 실행
        
        Args:
            signals: 진입/청산 신호 시리즈 (1=진입, -1=청산, 0=유지)
            prices: OHLCV DataFrame
            
        Returns:
            성과 지표 딕셔너리
        """
        # 포지션 계산 (누적)
        positions = signals.cumsum().clip(0, 1)
        
        # 수익률 계산
        returns = prices['close'].pct_change()
        strategy_returns = positions.shift(1) * returns
        
        # 거래 비용 차감
        trades = signals.abs()
        costs = trades * (self.config.commission_rate + self.config.slippage_rate)
        net_returns = strategy_returns - costs
        
        # 누적 수익
        equity = (1 + net_returns).cumprod() * self.config.initial_capital
        
        return self._calculate_metrics(equity, net_returns)
    
    def _calculate_metrics(self, equity: pd.Series, returns: pd.Series) -> Dict:
        """성과 지표 계산"""
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 * 60)  # 1분봉 기준
        max_dd = (equity / equity.cummax() - 1).min()
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'final_equity': equity.iloc[-1],
        }
```

### 사용 예시

```python
from src.backtest.engines.vectorized_engine import VectorizedEngine, VectorizedConfig

# 1000개 파라미터 조합 테스트
param_grid = {
    'entry_threshold': np.arange(0.02, 0.05, 0.005),
    'exit_threshold': np.arange(0.005, 0.02, 0.005),
}

engine = VectorizedEngine(VectorizedConfig())
results = []

for entry in param_grid['entry_threshold']:
    for exit in param_grid['exit_threshold']:
        signals = strategy.generate_signals(data, entry, exit)
        result = engine.run(signals, data)
        result['params'] = {'entry': entry, 'exit': exit}
        results.append(result)

# 상위 10개 선정
top_10 = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10]
```

---

## 🎯 Event-Driven Engine (정밀 검증용)

### 구조

```python
# src/backtest/engines/event_driven_engine.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from decimal import Decimal
import pandas as pd

@dataclass
class Order:
    """주문"""
    timestamp: pd.Timestamp
    symbol: str
    side: str           # 'BUY', 'SELL'
    quantity: Decimal
    order_type: str     # 'MARKET', 'LIMIT'
    price: Optional[Decimal] = None


@dataclass
class Fill:
    """체결"""
    timestamp: pd.Timestamp
    price: Decimal
    quantity: Decimal
    commission: Decimal
    slippage: Decimal


class EventDrivenEngine:
    """
    이벤트 기반 백테스트 엔진
    
    특징:
    - 실제 호가 데이터 사용
    - 동적 슬리피지 (VWAP, Market Impact)
    - Tick-by-tick 시뮬레이션
    
    용도: 최종 검증, 실거래 시뮬레이션
    """
    
    def __init__(
        self, 
        slippage_model: 'SlippageModel',
        initial_capital: float = 20_000_000
    ):
        self.slippage_model = slippage_model
        self.initial_capital = initial_capital
        self.position = Decimal('0')
        self.cash = Decimal(str(initial_capital))
        self.trades: List[Fill] = []
    
    def on_bar(self, bar: pd.Series, orderbook: Dict):
        """
        봉 데이터 수신 시 처리
        
        Args:
            bar: OHLCV 봉 데이터
            orderbook: 호가 스냅샷 {'bids': [...], 'asks': [...]}
        """
        # 전략에서 신호 생성
        signal = self.strategy.on_bar(bar)
        
        if signal == 1 and self.position == 0:
            # 진입
            self._execute_order(
                Order(bar.name, 'BTC', 'BUY', self._calc_qty(), 'MARKET'),
                orderbook
            )
        elif signal == -1 and self.position > 0:
            # 청산
            self._execute_order(
                Order(bar.name, 'BTC', 'SELL', self.position, 'MARKET'),
                orderbook
            )
    
    def _execute_order(self, order: Order, orderbook: Dict):
        """주문 실행 (슬리피지 모델 적용)"""
        
        # 슬리피지 계산
        exec_price, slippage = self.slippage_model.calculate(
            order, orderbook
        )
        
        # 수수료 계산
        commission = exec_price * order.quantity * Decimal('0.001')
        
        # 체결 기록
        fill = Fill(
            timestamp=order.timestamp,
            price=exec_price,
            quantity=order.quantity,
            commission=commission,
            slippage=slippage
        )
        self.trades.append(fill)
        
        # 포지션/잔고 업데이트
        if order.side == 'BUY':
            self.position += order.quantity
            self.cash -= exec_price * order.quantity + commission
        else:
            self.position -= order.quantity
            self.cash += exec_price * order.quantity - commission
```

---

## 📉 고급 슬리피지 모델

### VWAP 기반 슬리피지

```python
# src/backtest/slippage/vwap_slippage.py

from decimal import Decimal
from typing import Dict, Tuple, List

class VWAPSlippageModel:
    """
    VWAP 기반 슬리피지 모델
    
    실제 호가창을 순회하며 VWAP 계산
    대량 주문 시 슬리피지 증가 반영
    """
    
    def calculate(
        self, 
        order: 'Order', 
        orderbook: Dict
    ) -> Tuple[Decimal, Decimal]:
        """
        슬리피지 계산
        
        Args:
            order: 주문
            orderbook: {'bids': [[price, qty], ...], 'asks': [[price, qty], ...]}
            
        Returns:
            (체결가격, 슬리피지)
        """
        if order.side == 'BUY':
            levels = orderbook['asks']  # 매도 호가
        else:
            levels = orderbook['bids']  # 매수 호가
        
        # VWAP 계산
        remaining = order.quantity
        total_cost = Decimal('0')
        
        for price, qty in levels:
            price = Decimal(str(price))
            qty = Decimal(str(qty))
            
            fill_qty = min(remaining, qty)
            total_cost += price * fill_qty
            remaining -= fill_qty
            
            if remaining <= 0:
                break
        
        if remaining > 0:
            # 호가 부족 → 마지막 가격으로 나머지 체결 (페널티)
            last_price = Decimal(str(levels[-1][0]))
            penalty = last_price * Decimal('1.005')  # 0.5% 추가 슬리피지
            total_cost += penalty * remaining
        
        vwap = total_cost / order.quantity
        mid_price = (Decimal(str(orderbook['bids'][0][0])) + 
                     Decimal(str(orderbook['asks'][0][0]))) / 2
        slippage = abs(vwap - mid_price) / mid_price
        
        return vwap, slippage
```

### Market Impact 모델

```python
# src/backtest/slippage/market_impact.py

import math
from decimal import Decimal

class MarketImpactSlippageModel:
    """
    시장 충격 슬리피지 모델
    
    Almgren-Chriss 모델 기반
    주문 크기와 시장 유동성을 고려한 현실적 슬리피지
    """
    
    def __init__(
        self, 
        impact_coefficient: float = 0.1,
        volatility_window: int = 20
    ):
        self.impact_coefficient = impact_coefficient
        self.volatility_window = volatility_window
    
    def calculate(
        self, 
        order: 'Order', 
        orderbook: Dict,
        recent_volume: float,
        recent_volatility: float
    ) -> Tuple[Decimal, Decimal]:
        """
        시장 충격 기반 슬리피지 계산
        
        공식: slippage = η * σ * √(Q/ADV)
        
        - η: 충격 계수
        - σ: 최근 변동성
        - Q: 주문 수량
        - ADV: 평균 일 거래량
        """
        # 기본 VWAP 계산
        vwap_model = VWAPSlippageModel()
        base_price, _ = vwap_model.calculate(order, orderbook)
        
        # 시장 충격 계산
        order_ratio = float(order.quantity) / recent_volume
        market_impact = (
            self.impact_coefficient * 
            recent_volatility * 
            math.sqrt(order_ratio)
        )
        
        # 최종 가격
        if order.side == 'BUY':
            final_price = base_price * Decimal(str(1 + market_impact))
        else:
            final_price = base_price * Decimal(str(1 - market_impact))
        
        slippage = abs(final_price - base_price) / base_price
        
        return final_price, Decimal(str(slippage))
```

---

## 🔬 Walk-Forward Optimization

### 개요

과적합을 방지하기 위한 롤링 검증 방법입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                Walk-Forward Optimization                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Period 1: [=== Train ===][Test]                               │
│  Period 2:     [=== Train ===][Test]                           │
│  Period 3:         [=== Train ===][Test]                       │
│  Period 4:             [=== Train ===][Test]                   │
│  ...                                                            │
│                                                                 │
│  핵심 지표: WFE (Walk-Forward Efficiency)                       │
│  목표: WFE ≥ 50%                                                │
│                                                                 │
│  WFE = (OOS 성과 / IS 성과) × 100%                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 구현

```python
# src/backtest/validation/walk_forward.py

import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class WalkForwardConfig:
    """Walk-Forward 설정"""
    train_period: str = '6M'      # 훈련 기간
    test_period: str = '1M'       # 테스트 기간
    min_wfe: float = 0.5          # 최소 WFE (50%)


class WalkForwardValidator:
    """
    Walk-Forward Optimization 검증기
    
    목적: 과적합 감지 및 방지
    핵심: In-Sample과 Out-of-Sample 성과 비교
    """
    
    def __init__(self, config: WalkForwardConfig):
        self.config = config
    
    def run(
        self, 
        strategy_class: type,
        data: pd.DataFrame,
        param_grid: Dict
    ) -> Dict[str, Any]:
        """
        Walk-Forward 검증 실행
        
        Returns:
            {
                'wfe': Walk-Forward Efficiency,
                'is_overfit': 과적합 여부,
                'periods': 각 기간별 결과,
                'optimal_params': 권장 파라미터
            }
        """
        periods = self._create_periods(data)
        results = []
        
        for train_start, train_end, test_start, test_end in periods:
            # In-Sample: 파라미터 최적화
            train_data = data[train_start:train_end]
            optimal_params = self._optimize(strategy_class, train_data, param_grid)
            is_result = self._backtest(strategy_class, train_data, optimal_params)
            
            # Out-of-Sample: 검증
            test_data = data[test_start:test_end]
            oos_result = self._backtest(strategy_class, test_data, optimal_params)
            
            results.append({
                'period': f"{train_start} ~ {test_end}",
                'is_sharpe': is_result['sharpe_ratio'],
                'oos_sharpe': oos_result['sharpe_ratio'],
                'params': optimal_params
            })
        
        # WFE 계산
        avg_is = sum(r['is_sharpe'] for r in results) / len(results)
        avg_oos = sum(r['oos_sharpe'] for r in results) / len(results)
        wfe = avg_oos / avg_is if avg_is > 0 else 0
        
        return {
            'wfe': wfe,
            'is_overfit': wfe < self.config.min_wfe,
            'avg_is_sharpe': avg_is,
            'avg_oos_sharpe': avg_oos,
            'periods': results,
            'recommendation': self._get_recommendation(wfe)
        }
    
    def _get_recommendation(self, wfe: float) -> str:
        """WFE 기반 권장사항"""
        if wfe >= 0.8:
            return "✅ 우수 - 실거래 진행 가능"
        elif wfe >= 0.5:
            return "⚠️ 양호 - Paper Trading 권장"
        else:
            return "❌ 과적합 의심 - 전략 재검토 필요"
```

---

## 🔍 바이어스 감지

### Look-Ahead Bias 감지기

```python
# src/backtest/validation/bias_detector.py

import pandas as pd
from typing import List, Tuple

class LookAheadBiasDetector:
    """
    Look-Ahead Bias (미래 정보 사용) 감지기
    
    탐지 방법:
    1. 신호 생성 시점과 사용 데이터 시점 비교
    2. 비정상적으로 높은 성과 경고
    """
    
    def detect(
        self, 
        signals: pd.Series,
        data: pd.DataFrame
    ) -> List[Tuple[pd.Timestamp, str]]:
        """
        Look-Ahead Bias 탐지
        
        Returns:
            [(timestamp, warning_message), ...]
        """
        warnings = []
        
        # 1. 신호와 가격의 타임스탬프 정렬 확인
        for idx, signal in signals.items():
            if signal != 0:
                # 신호 시점의 데이터 확인
                if idx not in data.index:
                    warnings.append((idx, "신호 시점에 데이터 없음"))
                    continue
                
                # 다음 봉 가격과 비교
                try:
                    next_idx = data.index[data.index.get_loc(idx) + 1]
                    next_close = data.loc[next_idx, 'close']
                    current_close = data.loc[idx, 'close']
                    
                    # 진입 신호 후 즉시 유리한 방향으로 움직임 (의심)
                    if signal == 1 and next_close > current_close * 1.01:
                        warnings.append((idx, "진입 직후 1% 이상 상승 - Look-Ahead 의심"))
                    elif signal == -1 and next_close < current_close * 0.99:
                        warnings.append((idx, "청산 직후 1% 이상 하락 - Look-Ahead 의심"))
                        
                except (IndexError, KeyError):
                    pass
        
        # 2. 비정상적 성과 경고
        win_rate = self._calculate_win_rate(signals, data)
        if win_rate > 0.9:
            warnings.append((None, f"승률 {win_rate:.1%} - 비정상적으로 높음"))
        
        return warnings
    
    def _calculate_win_rate(self, signals: pd.Series, data: pd.DataFrame) -> float:
        """승률 계산"""
        # 구현
        pass
```

---

## 📊 성과 지표

### 수익률 지표

| 지표 | 설명 | 계산식 | 목표 |
|:---|:---|:---|:---|
| Total Return | 총 수익률 | (최종 - 초기) / 초기 | > 20%/년 |
| CAGR | 연평균 수익률 | (최종/초기)^(1/년수) - 1 | > 15% |
| Daily Return | 일별 수익률 | 일별 자산 변화율 | > 0 |

### 리스크 지표

| 지표 | 설명 | 목표 |
|:---|:---|:---|
| Sharpe Ratio | 위험 대비 수익 | > 1.0 |
| Max Drawdown | 최대 낙폭 | < 20% |
| Volatility | 변동성 | 낮을수록 좋음 |
| VaR (95%) | 95% 신뢰구간 손실 | < 5% |
| **WFE** | Walk-Forward Efficiency | **≥ 50%** |

### 거래 지표

| 지표 | 설명 | 목표 |
|:---|:---|:---|
| Win Rate | 승률 | > 50% |
| Profit Factor | 총이익/총손실 | > 1.5 |
| Avg Trade | 평균 거래 수익 | > 거래비용 |
| Avg Slippage | 평균 슬리피지 | < 0.1% |

---

## 📂 디렉토리 구조

```
src/backtest/
├── engines/
│   ├── __init__.py
│   ├── vectorized_engine.py      # 빠른 탐색용 (1000x)
│   └── event_driven_engine.py    # 정밀 검증용
│
├── slippage/
│   ├── __init__.py
│   ├── fixed_slippage.py         # 고정 비율
│   ├── vwap_slippage.py          # VWAP 기반
│   └── market_impact.py          # 시장 충격 모델
│
├── validation/
│   ├── __init__.py
│   ├── walk_forward.py           # Walk-Forward Optimization
│   ├── bias_detector.py          # Look-Ahead Bias 감지
│   └── monte_carlo.py            # 몬테카를로 시뮬레이션
│
└── metrics/
    ├── __init__.py
    ├── returns.py                # 수익률 지표
    ├── risk.py                   # 리스크 지표
    └── trade.py                  # 거래 지표
```

---

## ⚠️ 주의사항

### 바이어스 방지

| 바이어스 | 설명 | 방지 방법 |
|---------|------|----------|
| **Look-Ahead** | 미래 데이터 사용 | BiasDetector 사용 |
| **Survivorship** | 상폐 코인 제외 | 전체 데이터 사용 |
| **과최적화** | 파라미터 과다 | WFE ≥ 50% 확인 |

### 현실적 비용 적용

```python
# 보수적 비용 설정
config = BacktestConfig(
    commission_rate=0.001,    # 0.1% (업비트+바이낸스)
    slippage_rate=0.0005,     # 0.05% (기본)
    # Event-Driven에서는 VWAP/Market Impact 사용
)
```

---

*— 문서 끝 —*
