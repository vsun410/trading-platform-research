# 📐 김프 전략 상세 명세 Ver 3.0 (Technical Specification)

> **핵심 철학**: "절대 손절하지 않는다 (No Stop Loss)"
> 
> **문제 해결**: L자형 장세(김프 하락 후 횡보)에서 자금 묶임 문제를 **Breakout Rescue** 로직으로 해결

---

## 1. 전략 발전 과정 (History)

### Phase 1: 초기 전략 (Z-Score Reversion)
- **로직**: Z-Score -2.0 이탈 후 회귀 시 진입, +0.5% 수익 시 청산
- **결과**: ❌ 실패 - 목표 수익률 미도달, 장기 보유(물림) 발생
- **원인**: 환율 급등 구간에서 김프 구조적 하락/횡보, 반등 탄력 부족

### Phase 2: 수정 제안 및 기각
- **제안**: 환율 필터 + 타임컷(24시간 후 강제 청산)
- **결과**: ❌ 기각 - 횡보장 잦은 손절로 수수료 손실 누적
- **결정**: 손절 로직 폐기

### Phase 3: 최종 전략 확정 (Breakout Rescue)
- **개선안**:
  1. 환율 급등 필터: 환율이 추세보다 높으면 진입 금지 (방어)
  2. 무손절 존버: 진입 후 물리면 무기한 보유
  3. 구조대(Rescue) 로직: 볼린저밴드 상단 돌파 시 약수익(수수료+0.1%)으로 탈출
- **백테스트 결과** (3개월 스트레스 테스트):
  - 승률: **100%** (68전 68승)
  - 수익률: **+11.09%** (3개월 누적)
  - 특이사항: 거래의 **56%**가 Breakout Rescue로 탈출

---

## 2. 핵심 파라미터

| 항목 | 설정값 | 설명 |
|:---|:---|:---|
| **운용 자본** | 4,000만원 | 현물 50% / 선물 50% (레버리지 1x) |
| **예비비** | 5% (200만원) | 수수료/슬리피지 대응 |
| **수수료 (왕복)** | **0.38%** | Upbit(0.05×2) + Binance(0.04×2) + 슬리피지(0.1) |
| **정상 목표 (Track A)** | **0.7%** | Gross Profit 기준 (순수익 약 0.32%) |
| **탈출 목표 (Track B)** | **0.48%** | Breakout 시 최소 수익 (순수익 0.1% 확보) |
| **지표 기준** | 1분 봉 | 매매 판단은 1초 단위 실행 |
| **Z-Score Lookback** | **5분 (300초)** | 최근 최저점과 현재가 비교 |
| **BB Period** | 20 | 볼린저밴드 기간 |
| **BB StdDev** | 2.0 | 볼린저밴드 표준편차 배수 |

---

## 3. 계산식

### 3.1 김치프리미엄 계산

```python
kimp = ((upbit_price / (binance_price * exchange_rate)) - 1) * 100
```

| 변수 | 설명 | 소스 |
|:---|:---|:---|
| `upbit_price` | 업비트 BTC 가격 (KRW) | Upbit WebSocket |
| `binance_price` | 바이낸스 BTC 가격 (USDT) | Binance WebSocket |
| `exchange_rate` | USD/KRW 환율 | **TradingView FX_IDC:USDKRW** |

### 3.2 환율 이동평균 (12시간 MA)

```python
exchange_rate_ma_12h = SMA(exchange_rate, period=720)  # 1분봉 기준 720개
```

### 3.3 Z-Score 계산

```python
μ = SMA(kimp, period=20)  # 20분 이동평균
σ = STDDEV(kimp, period=20)  # 20분 표준편차
Z = (current_kimp - μ) / σ
```

### 3.4 볼린저밴드 (김프 % 대상)

```python
# ⚠️ 중요: 가격이 아닌 '김치프리미엄 %' 시계열 데이터를 대상으로 산출
BB_Middle = SMA(kimp, period=20)
BB_Upper = BB_Middle + (2.0 * STDDEV(kimp, period=20))
BB_Lower = BB_Middle - (2.0 * STDDEV(kimp, period=20))
```

---

## 4. 진입 로직 (Entry)

### 4.1 Step 1: 환율 필터 (안전장치)

```python
def check_exchange_rate_filter(current_rate, rate_ma_12h):
    """
    환율 급등 시 진입 금지
    
    조건: 현재 환율 > 환율_12시간_MA × 1.001 (0.1% 이상 급등)
    """
    threshold = rate_ma_12h * 1.001
    
    if current_rate > threshold:
        return False  # ❌ 진입 금지
    return True  # ✅ 진입 가능
```

### 4.2 Step 2: Z-Score 진입

```
┌─────────────────────────────────────────────────────────────┐
│                   Z-Score 진입 로직 (Ver 3.0)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [환율 필터 통과 확인]                                      │
│         │                                                   │
│         ↓                                                   │
│   [최근 5분 최저 Z-Score 확인]                               │
│         │                                                   │
│         ├─── 최저 Z ≤ -2.0 AND 현재 Z > -2.0                │
│         │         └──→ Level 1 진입 (40% 자본)              │
│         │                                                   │
│         └─── 최저 Z ≤ -2.5 AND 현재 Z > -2.5                │
│                   └──→ Level 2 진입 (60% 추가)              │
│                                                             │
│   ※ 급락 케이스: -2.5 직행 후 회귀 시 100% 한번에 진입       │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 진입 코드

```python
def check_entry_signal(z_history_5min: list, current_z: float, 
                       current_rate: float, rate_ma_12h: float) -> str:
    """
    진입 신호 확인 (Ver 3.0)
    
    Returns:
        'none': 진입 없음
        'level1': Level 1 진입 (40%)
        'level2': Level 2 추가 진입 (60%)
        'full': 전량 진입 (100%)
    """
    # Step 1: 환율 필터
    if current_rate > rate_ma_12h * 1.001:
        return 'none'  # 환율 급등 시 진입 금지
    
    if len(z_history_5min) < 5:
        return 'none'
    
    recent_min = min(z_history_5min)  # 최근 5분 최저점
    
    # Step 2: Z-Score 진입 판단
    # 급락 케이스: -2.5 직행 후 회귀
    if recent_min <= -2.5 and current_z > -2.5:
        if not position_exists():
            return 'full'  # 100% 진입
        elif level1_only():
            return 'level2'  # 60% 추가
    
    # 일반 케이스: -2.0 회귀
    elif recent_min <= -2.0 and current_z > -2.0:
        if not position_exists():
            return 'level1'  # 40% 진입
    
    return 'none'
```

---

## 5. 청산 로직 (Exit) - Dual Track

### 5.1 Track A: 정상 익절 (Target Hit)

```python
def check_target_exit(entry_kimp: float, current_kimp: float) -> bool:
    """
    정상 목표가 도달 확인
    
    조건: (현재김프 - 평단김프) >= 0.7%
    """
    profit_pct = current_kimp - entry_kimp
    return profit_pct >= 0.7
```

### 5.2 Track B: 돌파 탈출 (Breakout Rescue)

```python
def check_breakout_exit(entry_kimp: float, current_kimp: float, 
                        bb_upper: float) -> bool:
    """
    Breakout Rescue 조건 확인
    
    조건 1: (현재김프 - 평단김프) >= 0.48% (최소 마진 확보)
    조건 2: 현재김프 > 볼린저밴드 상단 (변동성 돌파 발생)
    """
    profit_pct = current_kimp - entry_kimp
    
    condition1 = profit_pct >= 0.48  # 최소 순익 0.1% 확보
    condition2 = current_kimp > bb_upper  # BB 상단 돌파
    
    return condition1 and condition2
```

### 5.3 통합 청산 로직

```python
def check_exit(position: dict, current_kimp: float, bb_upper: float) -> dict:
    """
    청산 조건 확인 (Dual Track)
    
    Returns:
        {'exit': bool, 'reason': 'Target' | 'Breakout' | None}
    """
    entry_kimp = position['entry_kimp']
    profit_pct = current_kimp - entry_kimp
    
    # Track A: 정상 익절 (우선순위 1)
    if profit_pct >= 0.7:
        return {'exit': True, 'reason': 'Target'}
    
    # Track B: Breakout Rescue (우선순위 2)
    if profit_pct >= 0.48 and current_kimp > bb_upper:
        return {'exit': True, 'reason': 'Breakout'}
    
    # 청산 조건 미충족 - 무한 보유 (No Stop Loss)
    return {'exit': False, 'reason': None}
```

---

## 6. 청산 비교표

| 항목 | Track A (정상) | Track B (Rescue) |
|:---|:---|:---|
| **조건** | 수익률 ≥ 0.7% | 수익률 ≥ 0.48% AND BB 상단 돌파 |
| **Gross Profit** | 0.7% | 0.48%+ |
| **순수익** | ~0.32% | ~0.10%+ |
| **발생 빈도** | 44% (백테스트) | 56% (백테스트) |
| **exit_reason** | `'Target'` | `'Breakout'` |

---

## 7. 환율 데이터 (TradingView)

### 7.1 데이터 소스

| 항목 | 값 |
|:---|:---|
| **심볼** | `FX_IDC:USDKRW` |
| **타임프레임** | 1분 |
| **갱신 주기** | 10초~1분 (캐싱) |
| **용도** | 김프 계산 + 12시간 MA 필터 |

### 7.2 TradingView 연동 코드

```python
# TradingView WebSocket 또는 REST API 연동
async def get_exchange_rate_from_tradingview():
    """
    TradingView FX_IDC:USDKRW 실시간 환율 조회
    """
    symbol = "FX_IDC:USDKRW"
    
    # TradingView 연동 로직
    # (구체적인 구현은 storage 레포 참조)
    
    return {
        'rate': current_rate,
        'ma_12h': calculate_ma(rate_history, 720),
        'timestamp': datetime.now()
    }
```

---

## 8. 상태 관리

### 8.1 포지션 상태

```python
position_state = {
    'is_active': False,
    'entry_timestamp': None,
    'entry_kimp': None,
    'entry_level': None,  # 'level1', 'level2', 'full'
    'invested_amount': 0,
    'btc_amount': 0,
    'upbit_entry_price': None,
    'binance_entry_price': None,
    'exchange_rate_at_entry': None,
}
```

### 8.2 거래 기록 (DB 저장)

```python
trade_record = {
    'trade_id': uuid4(),
    'entry_timestamp': datetime,
    'exit_timestamp': datetime,
    'entry_kimp': float,
    'exit_kimp': float,
    'gross_pnl_pct': float,
    'net_pnl_pct': float,
    'exit_reason': 'Target' | 'Breakout',  # ⚠️ 필수 저장
    'holding_duration_hours': float,
    'entry_level': str,
}
```

---

## 9. 실행 주기

| 작업 | 주기 | 설명 |
|:---|:---|:---|
| 가격 수집 | 실시간 (WebSocket) | Upbit/Binance |
| 환율 갱신 | 10초~1분 | TradingView 캐싱 |
| 지표 계산 | 1분 (Resampling) | Z-Score, BB |
| 진입/청산 체크 | **1초** | Tick 단위 루프 |

---

## 10. 향후 과제

- [ ] 실전 봇 개발 및 소액 테스트 진행
- [ ] 자금 관리: 최대 2주 이상 포지션 보유 가능성 대비 현금 비중 모니터링
- [ ] 가짜 돌파(Fakeout) 방지를 위한 스무딩 로직 (예: 3틱 평균) 추가 고려

---

**다음 문서**: [PARAMETERS.md](./PARAMETERS.md) - 파라미터 설정
