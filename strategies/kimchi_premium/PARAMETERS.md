# ⚙️ 파라미터 설정 Ver 3.0 (Parameters Configuration)

## 1. 핵심 파라미터 요약

### 1.1 자본 및 진입

| 카테고리 | 파라미터 | 기본값 | 범위 | 설명 |
|:---|:---|:---|:---|:---|
| **자본** | total | 40,000,000 | - | 총 자본금 (KRW) |
| | reserve_ratio | 0.05 | 0.03~0.10 | 예비비 비율 |
| **Z-Score** | window | 20 | 10~50 | 이동평균 기간 (분) |
| | lookback_seconds | **300** | 180~600 | 회귀 감지 기간 (**5분**) |
| | level1_threshold | -2.0 | -1.5~-2.5 | Level 1 진입 기준 |
| | level2_threshold | -2.5 | -2.0~-3.0 | Level 2 진입 기준 |
| **포지션** | level1_ratio | 0.4 | 0.3~0.5 | Level 1 투입 비율 |
| | level2_ratio | 0.6 | 0.5~0.7 | Level 2 투입 비율 |

### 1.2 환율 필터 (Ver 3.0 신규)

| 카테고리 | 파라미터 | 기본값 | 범위 | 설명 |
|:---|:---|:---|:---|:---|
| **환율 필터** | ma_period_hours | **12** | 6~24 | 환율 MA 기간 (시간) |
| | threshold_ratio | **1.001** | 1.0005~1.002 | 진입 차단 임계값 |
| | data_source | `FX_IDC:USDKRW` | - | TradingView 심볼 |

### 1.3 청산 (Dual Track)

| 카테고리 | 파라미터 | 기본값 | 범위 | 설명 |
|:---|:---|:---|:---|:---|
| **Track A** | target_profit | **0.007** | 0.005~0.010 | 정상 목표 (**0.7%**) |
| **Track B** | rescue_profit | **0.0048** | 0.004~0.006 | 탈출 최소 수익 (**0.48%**) |
| | bb_period | **20** | 15~30 | 볼린저밴드 기간 |
| | bb_stddev | **2.0** | 1.5~2.5 | 볼린저밴드 표준편차 |

---

## 2. config.yaml 전체 설정 (Ver 3.0)

```yaml
# ============================================================
# 김프 차익거래 전략 설정 파일 Ver 3.0
# ============================================================
# 핵심 철학: "절대 손절하지 않는다 (No Stop Loss)"

version: "3.0"

# 자본금 설정
capital:
  total: 40000000              # 총 자본금 (KRW)
  reserve_ratio: 0.05          # 예비비 비율 (5%)
  max_position_ratio: 0.95     # 최대 포지션 비율 (95%)

# ============================================================
# 환율 설정 (Ver 3.0 신규)
# ============================================================
exchange_rate:
  source: "tradingview"        # 데이터 소스
  symbol: "FX_IDC:USDKRW"      # TradingView 심볼
  update_interval: 10          # 갱신 주기 (초)
  cache_ttl: 60                # 캐시 유효시간 (초)
  
  # 환율 필터 (진입 안전장치)
  filter:
    enabled: true
    ma_period_minutes: 720     # 12시간 MA (1분봉 기준)
    threshold_ratio: 1.001     # 현재환율 > MA × 1.001 시 진입 금지

# ============================================================
# Z-Score 파라미터
# ============================================================
zscore:
  window: 20                   # 이동평균 기간 (분)
  lookback_seconds: 300        # 회귀 감지 기간 (5분 = 300초)
  level1_threshold: -2.0       # Level 1 진입 기준
  level2_threshold: -2.5       # Level 2 진입 기준

# ============================================================
# 볼린저밴드 파라미터 (Ver 3.0 신규)
# ============================================================
bollinger_band:
  target: "kimp_percent"       # ⚠️ 가격이 아닌 김프% 대상
  period: 20                   # 기간
  stddev: 2.0                  # 표준편차 배수

# ============================================================
# 청산 설정 (Dual Track)
# ============================================================
exit:
  strategy: "dual_track"       # Ver 3.0 청산 전략
  
  # Track A: 정상 익절
  track_a:
    enabled: true
    target_profit: 0.007       # 0.7% 목표
    
  # Track B: Breakout Rescue
  track_b:
    enabled: true
    min_profit: 0.0048         # 0.48% 최소 수익 (수수료+0.1% 확보)
    condition: "bb_upper_breakout"
    
  # 손절: 없음 (No Stop Loss)
  stop_loss:
    enabled: false             # ❌ 손절 비활성화
    note: "무손절 존버 전략"

# 포지션 설정
position:
  level1_ratio: 0.4            # Level 1 투입 비율 (40%)
  level2_ratio: 0.6            # Level 2 투입 비율 (60%)
  max_positions: 1             # 최대 동시 포지션 수

# 수수료 설정
fees:
  upbit: 0.0005                # 업비트 수수료 (0.05%)
  binance: 0.0004              # 바이낸스 수수료 (0.04%)
  slippage: 0.001              # 슬리피지 추정 (0.1%)
  total_roundtrip: 0.0038      # 왕복 총 비용 (0.38%)

# 코인 설정
coins:
  BTC:
    upbit_symbol: 'BTC/KRW'
    binance_symbol: 'BTC/USDT'
    min_order_size: 0.0001
    tick_size: 1000            # 원화 단위

# 거래소 설정
exchanges:
  upbit:
    type: 'spot'
    fee: 0.0005
    api_limit: 10              # 초당 API 호출 제한
  binance:
    type: 'futures'
    fee: 0.0004
    api_limit: 1200            # 분당 제한
    leverage: 1                # 델타 중립 (1배)

# API 키 설정 (환경변수 참조)
api_keys:
  upbit:
    access_key: ${UPBIT_ACCESS_KEY}
    secret_key: ${UPBIT_SECRET_KEY}
  binance:
    api_key: ${BINANCE_API_KEY}
    secret: ${BINANCE_SECRET}
  tradingview:
    # TradingView 연동 설정
    session_id: ${TRADINGVIEW_SESSION_ID}

# 데이터베이스 설정
database:
  type: supabase
  url: ${SUPABASE_URL}
  key: ${SUPABASE_KEY}
  # 또는 PostgreSQL 직접 연결
  # host: localhost
  # port: 5432
  # database: kimp_trading
  # user: trader
  # password: ${DB_PASSWORD}

# 모니터링 주기 (초)
monitoring:
  tick_interval: 1             # 진입/청산 체크 (1초)
  data_collection_interval: 60 # 데이터 저장 (1분)
  indicator_resample: 60       # 지표 계산 (1분봉)
  heartbeat_interval: 30       # 상태 확인 (30초)

# 알림 설정
notifications:
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
    # 알림 종류
    alerts:
      - entry
      - exit
      - error
      - emergency_stop
  discord:
    enabled: false
    webhook_url: ${DISCORD_WEBHOOK_URL}

# 로깅 설정
logging:
  level: INFO
  file: kimp_trading.log
  max_size: 10485760           # 10MB
  backup_count: 5
  
  # 거래 기록 별도 저장
  trade_log:
    enabled: true
    include_exit_reason: true  # Ver 3.0: Target/Breakout 구분

# 대시보드 설정
dashboard:
  streamlit:
    enabled: true
    host: localhost
    port: 8501
  telegram_bot:
    enabled: true
    commands:
      - /status                # 현재 상태
      - /stop                  # 긴급 정지
      - /resume                # 재개
```

---

## 3. 환경변수 설정 (.env)

```bash
# ============================================================
# 환경변수 설정 파일 (.env) Ver 3.0
# ============================================================

# 업비트 API
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

# 바이낸스 API
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_here

# TradingView (환율 데이터용)
TRADINGVIEW_SESSION_ID=your_tradingview_session_id

# Supabase (데이터베이스)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Telegram (알림 + 긴급 제어)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# 환경
ENVIRONMENT=production  # development | production
LOG_LEVEL=INFO
```

---

## 4. Ver 3.0 파라미터 변경 이력

| 항목 | Ver 2.x | Ver 3.0 | 변경 사유 |
|:---|:---|:---|:---|
| 목표 수익률 | 레벨별 차등 (0.5%/0.75%) | **통합 0.7%** | 백테스트 결과 최적화 |
| 탈출 목표 | 없음 | **0.48%** | Breakout Rescue 도입 |
| Z-Score Lookback | 미명시 | **5분 (300초)** | 회귀 감지 정확도 향상 |
| 환율 필터 | 없음 | **12시간 MA × 1.001** | 환율 급등 시 진입 방어 |
| 손절 | 타임컷 고려 | **완전 비활성화** | 무손절 철학 확정 |
| 환율 소스 | 한국은행/ExchangeRate | **TradingView** | 데이터 품질 향상 |

---

## 5. 파라미터 튜닝 가이드

### 5.1 환율 필터 임계값

| threshold_ratio | 특성 | 추천 상황 |
|:---|:---|:---|
| 1.0005 | 민감함 (많은 진입 차단) | 보수적 운영 |
| **1.001** | **균형** | **일반적 상황** |
| 1.002 | 둔감함 (적은 차단) | 공격적 운영 |

### 5.2 Breakout 최소 수익

| min_profit | 순수익 | 특성 |
|:---|:---|:---|
| 0.004 | ~0.02% | 빠른 탈출, 낮은 순익 |
| **0.0048** | **~0.10%** | **균형 (권장)** |
| 0.006 | ~0.22% | 늦은 탈출, 높은 순익 |

### 5.3 볼린저밴드 민감도

| bb_stddev | 특성 | 발생 빈도 |
|:---|:---|:---|
| 1.5 | 민감함 (잦은 돌파) | 높음 |
| **2.0** | **균형** | **중간** |
| 2.5 | 둔감함 (드문 돌파) | 낮음 |

---

## 6. 백테스트용 파라미터 범위

```python
# Ver 3.0 파라미터 최적화 그리드
PARAM_GRID = {
    # 진입
    'zscore_window': [15, 20, 25],
    'zscore_lookback_seconds': [180, 300, 420],
    'level1_threshold': [-1.75, -2.0, -2.25],
    'level2_threshold': [-2.25, -2.5, -2.75],
    
    # 환율 필터
    'exchange_rate_ma_hours': [6, 12, 24],
    'exchange_rate_threshold': [1.0005, 1.001, 1.0015],
    
    # 청산
    'target_profit': [0.006, 0.007, 0.008],
    'rescue_min_profit': [0.004, 0.0048, 0.0055],
    'bb_stddev': [1.5, 2.0, 2.5],
}

# 제약 조건
CONSTRAINTS = {
    'level2_threshold < level1_threshold': True,
    'target_profit > total_fee': True,  # > 0.0038
    'rescue_min_profit > total_fee': True,  # > 0.0038
}
```

---

**다음 문서**: [RISK_MANAGEMENT.md](./RISK_MANAGEMENT.md) - 리스크 관리
