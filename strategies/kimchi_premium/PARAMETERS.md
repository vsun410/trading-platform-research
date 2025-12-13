# ⚙️ 김치프리미엄 전략 파라미터 명세 (Ver 3.0)

## 1. 전략 파라미터 개요

### 1.1 버전 히스토리

| 버전 | 날짜 | 변경사항 |
|:---|:---|:---|
| 1.0 | 2025-12-11 | 초기 Z-Score 기반 전략 |
| 2.0 | 2025-12-12 | 손절 로직 폐기, No Stop Loss 확정 |
| **3.0** | **2025-12-14** | **환율 필터 + Breakout Rescue 추가** |

### 1.2 파라미터 분류

```
┌─────────────────────────────────────────────────────────────┐
│                    Parameter Categories                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   1. Capital       자본금 관련 파라미터                       │
│   2. Entry         진입 조건 파라미터                         │
│   3. Exit          청산 조건 파라미터 (Dual Track)            │
│   4. ExchangeRate  환율 필터 파라미터 [NEW in 3.0]           │
│   5. Technical     기술적 지표 파라미터                       │
│   6. Fee           수수료 파라미터                            │
│   7. Execution     실행 관련 파라미터                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Capital (자본금 파라미터)

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `TOTAL_CAPITAL` | 40,000,000 | KRW | 총 운용 자본금 |
| `RESERVE_RATIO` | 0.05 | float | 예비비 비율 (5%) |
| `TRADING_CAPITAL` | 38,000,000 | KRW | 실제 운용 자본 (95%) |
| `UPBIT_ALLOCATION` | 0.50 | float | 업비트 배분 (현물 LONG) |
| `BINANCE_ALLOCATION` | 0.50 | float | 바이낸스 배분 (선물 SHORT) |

### 계산식
```python
TRADING_CAPITAL = TOTAL_CAPITAL * (1 - RESERVE_RATIO)
# 38,000,000 = 40,000,000 * 0.95
```

---

## 3. Entry (진입 파라미터)

### 3.1 Z-Score 진입 조건

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `ZSCORE_LEVEL1_THRESHOLD` | -2.0 | float | Level 1 진입 임계값 |
| `ZSCORE_LEVEL2_THRESHOLD` | -2.5 | float | Level 2 진입 임계값 |
| `ZSCORE_LOOKBACK_SECONDS` | 300 | int | 회귀 판단 Lookback (5분) |
| `ZSCORE_WINDOW` | 20 | int | Z-Score 계산 기간 (20개 1분봉) |

### 3.2 분할 진입 비율

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `LEVEL1_RATIO` | 0.40 | float | Level 1 진입 비율 (40%) |
| `LEVEL2_RATIO` | 0.60 | float | Level 2 추가 비율 (60%) |

### 진입 자본 계산
```python
LEVEL1_CAPITAL = TRADING_CAPITAL * LEVEL1_RATIO
# 15,200,000 = 38,000,000 * 0.40

LEVEL2_CAPITAL = TRADING_CAPITAL * LEVEL2_RATIO  
# 22,800,000 = 38,000,000 * 0.60
```

---

## 4. Exit (청산 파라미터) - Dual Track

### 4.1 Track A: 정상 익절

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `TARGET_PROFIT_PCT` | 0.70 | % | 목표 수익률 (Gross) |
| `TARGET_NET_PROFIT_PCT` | 0.32 | % | 순수익률 (수수료 차감 후) |

### 4.2 Track B: Breakout Rescue [NEW in 3.0]

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `BREAKOUT_MIN_PROFIT_PCT` | 0.48 | % | 최소 마진 (수수료 + 0.1%) |
| `BREAKOUT_NET_PROFIT_PCT` | 0.10 | % | Breakout 시 최소 순익 |
| `BB_PERIOD` | 20 | int | 볼린저 밴드 기간 |
| `BB_STD_MULT` | 2.0 | float | 볼린저 밴드 표준편차 배수 |

### 4.3 exit_reason 값

| 값 | 설명 |
|:---|:---|
| `'Target'` | Track A: 정상 목표가(0.7%) 도달 |
| `'Breakout'` | Track B: BB 상단 돌파 + 0.48% 이상 |

---

## 5. ExchangeRate (환율 필터 파라미터) [NEW in 3.0]

### 5.1 환율 데이터 소스

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `FX_SOURCE` | `'TradingView'` | str | 환율 데이터 소스 |
| `FX_SYMBOL` | `'FX_IDC:USDKRW'` | str | TradingView 심볼 |
| `FX_UPDATE_INTERVAL` | 60 | sec | 환율 갱신 주기 |
| `FX_CACHE_TTL` | 60 | sec | 캐시 유효 시간 |

### 5.2 환율 필터 조건

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `FX_MA_PERIOD` | 720 | int | 환율 이동평균 기간 (12시간 = 720분) |
| `FX_SURGE_THRESHOLD` | 1.001 | float | 급등 판단 임계값 (+0.1%) |

### 환율 필터 로직
```python
# 환율 급등 시 진입 차단
def is_fx_blocked(current_rate: float, ma_12h: float) -> bool:
    return current_rate > ma_12h * FX_SURGE_THRESHOLD

# 예시
# current_rate = 1,350.0
# ma_12h = 1,345.0
# threshold = 1,345.0 * 1.001 = 1,346.345
# 1,350.0 > 1,346.345 → True (진입 차단)
```

---

## 6. Technical (기술적 지표 파라미터)

### 6.1 Z-Score 계산

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `ZSCORE_WINDOW` | 20 | int | 이동평균/표준편차 기간 |
| `ZSCORE_MIN_DATA` | 20 | int | 최소 필요 데이터 수 |

### 6.2 볼린저 밴드 (김프 % 기반)

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `BB_PERIOD` | 20 | int | MA 기간 |
| `BB_STD_MULT` | 2.0 | float | 표준편차 배수 |
| `BB_DATA_TYPE` | `'kimp_pct'` | str | 대상 데이터 (가격 아닌 김프%) |

### 계산식
```python
def calculate_zscore(kimp_series: list, window: int = 20) -> float:
    if len(kimp_series) < window:
        return 0.0
    
    recent = kimp_series[-window:]
    mean = sum(recent) / window
    std = (sum((x - mean) ** 2 for x in recent) / window) ** 0.5
    
    if std == 0:
        return 0.0
    
    return (kimp_series[-1] - mean) / std

def calculate_bb_upper(kimp_series: list, period: int = 20, mult: float = 2.0) -> float:
    if len(kimp_series) < period:
        return float('inf')
    
    recent = kimp_series[-period:]
    mean = sum(recent) / period
    std = (sum((x - mean) ** 2 for x in recent) / period) ** 0.5
    
    return mean + mult * std
```

---

## 7. Fee (수수료 파라미터)

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `UPBIT_FEE` | 0.0005 | float | 업비트 수수료 (0.05%) |
| `BINANCE_FEE` | 0.0004 | float | 바이낸스 수수료 (0.04%, 시장가) |
| `SLIPPAGE` | 0.001 | float | 슬리피지 (0.1%) |
| `TOTAL_ROUNDTRIP_FEE` | 0.0038 | float | 왕복 총 비용 (0.38%) |

### 수수료 계산
```python
TOTAL_ROUNDTRIP_FEE = (
    UPBIT_FEE * 2 +      # 0.05% × 2 = 0.10%
    BINANCE_FEE * 2 +    # 0.04% × 2 = 0.08%
    SLIPPAGE * 2         # 0.10% × 2 = 0.20%
)
# = 0.38%
```

---

## 8. Execution (실행 파라미터)

| 파라미터 | 값 | 타입 | 설명 |
|:---|:---|:---|:---|
| `DATA_TICK_INTERVAL` | 1 | sec | 데이터 수신 주기 |
| `INDICATOR_INTERVAL` | 60 | sec | 지표 계산 주기 (1분봉) |
| `SIGNAL_CHECK_INTERVAL` | 1 | sec | 신호 판단 주기 |
| `ORDER_TYPE` | `'market'` | str | 주문 유형 (시장가) |
| `MAX_RETRY` | 3 | int | 주문 실패 시 재시도 횟수 |
| `RETRY_DELAY` | 1 | sec | 재시도 간격 |

---

## 9. 전체 설정 파일 (config.yaml)

```yaml
# Ver 3.0 Configuration
version: "3.0"
updated_at: "2025-12-14"

# Capital
capital:
  total: 40000000
  reserve_ratio: 0.05
  trading_capital: 38000000
  upbit_allocation: 0.50
  binance_allocation: 0.50

# Entry
entry:
  zscore:
    level1_threshold: -2.0
    level2_threshold: -2.5
    lookback_seconds: 300
    window: 20
  ratios:
    level1: 0.40
    level2: 0.60

# Exit - Dual Track
exit:
  track_a:
    target_profit_pct: 0.70
    target_net_profit_pct: 0.32
  track_b:
    breakout_min_profit_pct: 0.48
    breakout_net_profit_pct: 0.10
    bb_period: 20
    bb_std_mult: 2.0

# Exchange Rate Filter [NEW in 3.0]
exchange_rate:
  source: "TradingView"
  symbol: "FX_IDC:USDKRW"
  update_interval: 60
  cache_ttl: 60
  filter:
    ma_period: 720  # 12시간
    surge_threshold: 1.001  # +0.1%

# Technical
technical:
  zscore:
    window: 20
    min_data: 20
  bollinger:
    period: 20
    std_mult: 2.0
    data_type: "kimp_pct"

# Fees
fees:
  upbit: 0.0005
  binance: 0.0004
  slippage: 0.001
  total_roundtrip: 0.0038

# Execution
execution:
  data_tick_interval: 1
  indicator_interval: 60
  signal_check_interval: 1
  order_type: "market"
  max_retry: 3
  retry_delay: 1
```

---

**버전**: 3.0  
**작성일**: 2025-12-14  
**레포**: trading-platform-research
