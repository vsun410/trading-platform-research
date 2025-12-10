# 백테스트 가이드

## 📋 개요

전략의 과거 성과를 검증하는 백테스트 실행 방법을 설명합니다.

## 🏗️ 백테스트 엔진 구조

```python
from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd

@dataclass
class BacktestConfig:
    """백테스트 설정"""
    start_date: str           # '2023-01-01'
    end_date: str             # '2024-12-31'
    initial_capital: float    # 20_000_000 (2천만원)
    commission_rate: float    # 0.001 (0.1%)
    slippage_rate: float      # 0.0005 (0.05%)

@dataclass
class BacktestResult:
    """백테스트 결과"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: List[Dict[str, Any]]
    equity_curve: pd.Series

class BacktestEngine:
    """벡터화 백테스트 엔진"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        
    def run(self, strategy, data: pd.DataFrame) -> BacktestResult:
        """
        백테스트 실행
        
        Args:
            strategy: BaseStrategy 구현체
            data: OHLCV DataFrame
            
        Returns:
            BacktestResult
        """
        # 구현 예정
        pass
```

## 🚀 실행 방법

### 기본 사용법

```python
from src.backtest.engine import BacktestEngine, BacktestConfig
from src.strategies.kimp.cash_carry import KimpCashCarryStrategy
from src.data.fetcher import DataFetcher

# 1. 데이터 로드
fetcher = DataFetcher()
data = fetcher.get_ohlcv(
    symbols=['BTC'],
    start='2023-01-01',
    end='2024-12-31',
    interval='1m'
)

# 2. 전략 생성
strategy = KimpCashCarryStrategy({
    'entry_threshold': 0.03,
    'exit_threshold': 0.01
})

# 3. 백테스트 설정
config = BacktestConfig(
    start_date='2023-01-01',
    end_date='2024-12-31',
    initial_capital=20_000_000,  # 2천만원
    commission_rate=0.001,
    slippage_rate=0.0005
)

# 4. 실행
engine = BacktestEngine(config)
result = engine.run(strategy, data)

# 5. 결과 확인
print(f"총 수익률: {result.total_return:.2%}")
print(f"샤프 비율: {result.sharpe_ratio:.2f}")
print(f"최대 낙폭: {result.max_drawdown:.2%}")
```

### Jupyter 노트북 사용

```bash
jupyter lab notebooks/01_kimp_analysis.ipynb
```

## 📊 성과 지표

### 수익률 지표

| 지표 | 설명 | 계산식 |
|:---|:---|:---|
| Total Return | 총 수익률 | (최종 자산 - 초기 자산) / 초기 자산 |
| CAGR | 연평균 수익률 | (최종/초기)^(1/년수) - 1 |
| Daily Return | 일별 수익률 | 일별 자산 변화율 |

### 리스크 지표

| 지표 | 설명 | 목표 |
|:---|:---|:---|
| Sharpe Ratio | 위험 대비 수익 | > 1.0 |
| Max Drawdown | 최대 낙폭 | < 20% |
| Volatility | 변동성 | 낮을수록 좋음 |
| VAR (95%) | 95% 신뢰구간 손실 | 관리 가능 수준 |

### 거래 지표

| 지표 | 설명 | 목표 |
|:---|:---|:---|
| Win Rate | 승률 | > 50% |
| Profit Factor | 총이익/총손실 | > 1.5 |
| Avg Trade | 평균 거래 수익 | > 0 |

## ⚙️ 설정 옵션

### 수수료 설정

```python
# 업비트: 0.05%
# 바이낸스 현물: 0.1%
# 바이낸스 선물: 0.04% (메이커), 0.02% (테이커)

config = BacktestConfig(
    commission_rate=0.001,  # 0.1% (보수적)
    slippage_rate=0.0005    # 0.05%
)
```

### 자본금 설정

```python
config = BacktestConfig(
    initial_capital=20_000_000,  # 2천만원
    # ...
)
```

## 🔬 검증 방법

### Walk-Forward 검증

```python
from src.backtest.validation import WalkForwardValidator

validator = WalkForwardValidator(
    train_period='6M',   # 6개월 학습
    test_period='1M',    # 1개월 테스트
    n_splits=12          # 12번 반복
)

results = validator.run(strategy, data)
```

### Out-of-Sample 테스트

```python
# In-Sample: 2023-01-01 ~ 2024-06-30
# Out-of-Sample: 2024-07-01 ~ 2024-12-31

in_sample_data = data['2023-01-01':'2024-06-30']
out_sample_data = data['2024-07-01':'2024-12-31']

# In-Sample로 최적화
optimized_params = optimizer.run(strategy, in_sample_data)

# Out-of-Sample로 검증
final_result = engine.run(
    strategy.with_params(optimized_params),
    out_sample_data
)
```

## ⚠️ 주의사항

1. **Look-ahead Bias**: 미래 데이터 사용 금지
2. **Survivorship Bias**: 상폐 코인 포함
3. **과최적화**: 파라미터 수 최소화
4. **거래비용**: 현실적인 수수료/슬리피지 적용
