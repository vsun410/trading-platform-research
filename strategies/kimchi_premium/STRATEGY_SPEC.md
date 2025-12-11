# 📐 김프 전략 상세 명세 (Technical Specification)

## 1. 계산식

### 1.1 김치프리미엄 계산

```python
kimp = ((upbit_price / (binance_price * exchange_rate)) - 1) * 100
```

| 변수 | 설명 | 예시 |
|:---|:---|:---|
| `upbit_price` | 업비트 BTC 가격 (KRW) | 150,000,000 |
| `binance_price` | 바이낸스 BTC 가격 (USDT) | 100,000 |
| `exchange_rate` | USD/KRW 환율 | 1,450 |

**예시 계산:**
```
kimp = ((150,000,000 / (100,000 * 1,450)) - 1) * 100
     = ((150,000,000 / 145,000,000) - 1) * 100
     = (1.0345 - 1) * 100
     = 3.45%
```

### 1.2 김프 이동평균 (SMA)

```python
SMA = (1/N) * Σ(kimp[t-i]) for i in range(N)
```

- **N**: 기간 (기본값: 20)
- **t**: 현재 시점

### 1.3 표준편차 계산

```python
σ = sqrt((1/N) * Σ(kimp[i] - μ)²)
```

### 1.4 Z-Score 계산

```python
Z = (current_kimp - μ) / σ
```

| Z-Score | 해석 |
|:---|:---|
| Z > 2.0 | 김프 과대 (역사적 평균 대비 높음) |
| -2.0 < Z < 2.0 | 정상 범위 |
| Z < -2.0 | 김프 과소 (역사적 평균 대비 낮음) |

## 2. 진입 조건

### 2.1 Z-Score 기반 분할 진입

```
┌─────────────────────────────────────────────────────┐
│                   Z-Score 진입 로직                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│   Z = -1.5  ────────────────────── 관망             │
│                                                     │
│   Z = -2.0  ══════════════════════ Level 1 트리거   │
│             │                                       │
│             ↓ 이탈 후 회귀 감지                      │
│             │                                       │
│   Z > -2.0  ══════════════════════ Level 1 진입     │
│             (40% 자본 투입)                          │
│                                                     │
│   Z = -2.5  ══════════════════════ Level 2 트리거   │
│             │                                       │
│             ↓ 이탈 후 회귀 감지                      │
│             │                                       │
│   Z > -2.5  ══════════════════════ Level 2 진입     │
│             (60% 추가 투입)                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 진입 시나리오

**시나리오 A: 정상 진입**
```
1. Z-Score가 -2.0 아래로 하락 (이탈)
2. Z-Score가 -2.0 위로 회복 (회귀)
3. Level 1 진입 (40%)
4. (선택) Z-Score가 -2.5 아래로 하락 후 회복 시 Level 2 추가 (60%)
```

**시나리오 B: 급락 직행**
```
1. Z-Score가 -2.0을 건너뛰고 -2.5 직행
2. Z-Score가 -2.5 위로 회복 (회귀)
3. 전량 진입 (100%)
```

### 2.3 진입 상태 플래그

```python
entry_state = {
    'level1_triggered': False,  # Z <= -2.0 도달 여부
    'level2_triggered': False,  # Z <= -2.5 도달 여부
    'level1_entered': False,    # Level 1 진입 여부
    'level2_entered': False,    # Level 2 진입 여부
    'position_count': 0,        # 현재 포지션 수 (최대 1)
}
```

## 3. 청산 조건

### 3.1 목표 수익률 기반 청산

| 진입 패턴 | 목표 수익률 | 수수료 후 순수익 |
|:---|:---|:---|
| Level 1만 (40%) | 0.5% | 0.12% |
| Level 2만 (60%) | 0.75% | 0.37% |
| Level 1+2 (100%) | 0.7% | 0.32% |

### 3.2 청산 로직

```python
def check_exit_condition(position, current_pnl):
    """
    청산 조건 확인
    
    Args:
        position: 현재 포지션 정보
        current_pnl: 현재 PnL (투입자본 대비 %)
    
    Returns:
        bool: 청산 여부
    """
    target = {
        'level1_only': 0.005,    # 0.5%
        'level2_only': 0.0075,   # 0.75%
        'combined': 0.007,       # 0.7%
    }
    
    if position['level1'] and position['level2']:
        return current_pnl >= target['combined']
    elif position['level1']:
        return current_pnl >= target['level1_only']
    elif position['level2']:
        return current_pnl >= target['level2_only']
    
    return False
```

## 4. 포지션 관리

### 4.1 자본 배분

```
총 자본: 4,000만원
├── 예비비: 200만원 (5%)
├── 업비트 현물: 1,900만원 (47.5%)
└── 바이낸스 선물: 1,900만원 (47.5%)
```

### 4.2 포지션 제약

| 제약 | 값 | 설명 |
|:---|:---|:---|
| 최대 포지션 | 1 | 청산 전까지 추가 진입 불가 |
| 예비비 | 5% | 수수료/슬리피지 대응 |
| 레버리지 | 1x | 델타 중립 유지 |

### 4.3 수량 계산

```python
def calculate_btc_amount(capital_krw, upbit_price, level_ratio):
    """
    BTC 수량 계산
    
    Args:
        capital_krw: 투입 자본 (KRW)
        upbit_price: 업비트 BTC 가격
        level_ratio: 진입 비율 (0.4 or 0.6)
    
    Returns:
        float: BTC 수량
    """
    available = capital_krw * 0.95  # 예비비 제외
    invest_amount = available * level_ratio
    btc_amount = invest_amount / upbit_price
    
    return round(btc_amount, 4)  # 소수점 4자리
```

## 5. 주문 실행

### 5.1 동시 주문 (Hedge Entry)

```python
async def execute_hedge_entry(amount, upbit_price, binance_price):
    """
    헤지 포지션 동시 진입
    
    Args:
        amount: 투입 금액 (KRW)
        upbit_price: 업비트 현재가
        binance_price: 바이낸스 현재가
    
    Returns:
        dict: 주문 결과
    """
    btc_amount = amount / upbit_price
    
    # 동시 실행
    tasks = [
        execute_upbit_buy(btc_amount, upbit_price),
        execute_binance_short(btc_amount, binance_price)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 한쪽만 체결된 경우 롤백
    if any(isinstance(r, Exception) for r in results):
        await rollback_orders(results)
        raise Exception("헤지 진입 실패")
    
    return {'upbit': results[0], 'binance': results[1]}
```

### 5.2 주문 유형

| 거래소 | 주문 유형 | 이유 |
|:---|:---|:---|
| 업비트 | 시장가 | 빠른 체결 우선 |
| 바이낸스 | 시장가 | 동시성 보장 |

### 5.3 롤백 처리

```python
async def rollback_orders(upbit_order, binance_order):
    """
    실패한 주문 롤백
    """
    # 업비트만 체결된 경우 - 즉시 매도
    if not isinstance(upbit_order, Exception):
        await execute_upbit_sell(upbit_order['filled'], None)
    
    # 바이낸스만 체결된 경우 - 포지션 종료
    if not isinstance(binance_order, Exception):
        await execute_binance_close(binance_order['filled'], None)
```

## 6. 환율 API

### 6.1 API 우선순위

| 순위 | API | 장점 | 단점 |
|:---|:---|:---|:---|
| 1 | 한국은행 API | 공신력 | Rate Limit |
| 2 | ExchangeRate-API | 빠름 | 약간의 지연 |

### 6.2 환율 조회 코드

```python
def get_exchange_rate():
    """
    환율 조회 (USD/KRW)
    """
    try:
        # 1순위: 한국은행 API
        response = requests.get(
            'https://ecos.bok.or.kr/api/...',
            timeout=5
        )
        return response.json()['rate']
    except:
        # 2순위: ExchangeRate-API
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD'
        )
        return response.json()['rates']['KRW']
```

---

**다음 문서**: [PARAMETERS.md](./PARAMETERS.md) - 파라미터 설정
