# ⚙️ 파라미터 설정 (Parameters Configuration)

## 1. 핵심 파라미터 요약

| 카테고리 | 파라미터 | 기본값 | 범위 | 설명 |
|:---|:---|:---|:---|:---|
| **자본** | total | 40,000,000 | - | 총 자본금 (KRW) |
| | reserve_ratio | 0.05 | 0.03~0.10 | 예비비 비율 |
| **Z-Score** | window | 20 | 10~50 | 이동평균 기간 |
| | lookback_hours | 168 | 24~336 | 히스토리 보관 (시간) |
| | level1_threshold | -2.0 | -1.5~-2.5 | Level 1 진입 기준 |
| | level2_threshold | -2.5 | -2.0~-3.0 | Level 2 진입 기준 |
| **포지션** | level1_ratio | 0.4 | 0.3~0.5 | Level 1 투입 비율 |
| | level2_ratio | 0.6 | 0.5~0.7 | Level 2 투입 비율 |
| **목표** | level1_only | 0.005 | 0.003~0.008 | Level 1 목표 수익률 |
| | level2_only | 0.0075 | 0.005~0.010 | Level 2 목표 수익률 |
| | combined | 0.007 | 0.005~0.010 | 합산 목표 수익률 |

## 2. config.yaml 전체 설정

```yaml
# ============================================================
# 김프 차익거래 전략 설정 파일
# ============================================================

# 자본금 설정
capital:
  total: 40000000              # 총 자본금 (KRW)
  reserve_ratio: 0.05          # 예비비 비율 (5%)
  max_position_ratio: 0.95     # 최대 포지션 비율 (95%)

# Z-Score 파라미터
zscore:
  window: 20                   # 이동평균 기간
  lookback_hours: 168          # 히스토리 보관 (1주일)
  level1_threshold: -2.0       # Level 1 진입 기준
  level2_threshold: -2.5       # Level 2 진입 기준

# 포지션 설정
position:
  level1_ratio: 0.4            # Level 1 투입 비율 (40%)
  level2_ratio: 0.6            # Level 2 투입 비율 (60%)
  max_positions: 1             # 최대 동시 포지션 수

# 목표 수익률
target_returns:
  level1_only: 0.005           # 0.5%
  level2_only: 0.0075          # 0.75%
  combined: 0.007              # 0.7%

# 수수료 설정
fees:
  upbit: 0.0005                # 업비트 수수료 (0.05%)
  binance: 0.0004              # 바이낸스 수수료 (0.04%)
  slippage: 0.001              # 슬리피지 추정 (0.1%)

# 코인 설정
coins:
  BTC:
    upbit_symbol: 'BTC/KRW'
    binance_symbol: 'BTC/USDT'
    min_order_size: 0.0001
    tick_size: 1000            # 원화 단위
  ETH:
    upbit_symbol: 'ETH/KRW'
    binance_symbol: 'ETH/USDT'
    min_order_size: 0.001
    tick_size: 100
  XRP:
    upbit_symbol: 'XRP/KRW'
    binance_symbol: 'XRP/USDT'
    min_order_size: 1
    tick_size: 1

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

# 데이터베이스 설정
database:
  host: localhost
  port: 5432
  database: kimp_trading
  user: trader
  password: ${DB_PASSWORD}

# 모니터링 주기 (초)
monitoring:
  data_collection_interval: 60     # 1분
  entry_check_interval: 3600       # 1시간
  exit_check_interval: 60          # 1분
  heartbeat_interval: 30           # 30초

# 알림 설정
notifications:
  discord:
    enabled: true
    webhook_url: ${DISCORD_WEBHOOK_URL}
  telegram:
    enabled: false
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}

# 로깅 설정
logging:
  level: INFO
  file: kimp_trading.log
  max_size: 10485760             # 10MB
  backup_count: 5

# 긴급 정지 조건
emergency:
  max_drawdown: 0.05             # 최대 손실 5%
  api_error_threshold: 5         # 연속 API 에러 5회
  network_latency_threshold: 1000  # 네트워크 지연 1초
```

## 3. 환경변수 설정 (.env)

```bash
# ============================================================
# 환경변수 설정 파일 (.env)
# ============================================================

# 업비트 API
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

# 바이낸스 API
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_here

# 데이터베이스
DB_PASSWORD=your_database_password_here

# 알림
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# 환경
ENVIRONMENT=production  # development | production
LOG_LEVEL=INFO
```

## 4. 파라미터 튜닝 가이드

### 4.1 Z-Score Window

| 값 | 특성 | 추천 상황 |
|:---|:---|:---|
| 10 | 민감함, 잦은 신호 | 변동성 큰 시장 |
| 20 | **균형** | 일반적 상황 |
| 50 | 둔감함, 적은 신호 | 안정적 시장 |

### 4.2 진입 임계값

| Level 1 | Level 2 | 특성 |
|:---|:---|:---|
| -1.5 | -2.0 | 공격적 (잦은 진입) |
| **-2.0** | **-2.5** | **균형** |
| -2.5 | -3.0 | 보수적 (적은 진입) |

### 4.3 목표 수익률

| 목표 | 수수료 후 | 체결 빈도 |
|:---|:---|:---|
| 0.3% | -0.08% | 높음 (손실) |
| 0.5% | 0.12% | 중간 |
| **0.7%** | **0.32%** | **권장** |
| 1.0% | 0.62% | 낮음 |

## 5. 백테스트용 파라미터 범위

```python
# 파라미터 최적화용 그리드
PARAM_GRID = {
    'zscore_window': [10, 15, 20, 25, 30],
    'level1_threshold': [-1.5, -1.75, -2.0, -2.25, -2.5],
    'level2_threshold': [-2.0, -2.25, -2.5, -2.75, -3.0],
    'target_return': [0.004, 0.005, 0.006, 0.007, 0.008],
}

# 제약 조건
CONSTRAINTS = {
    'level2_threshold < level1_threshold': True,
    'target_return > total_fee': True,  # 0.0038
}
```

---

**다음 문서**: [RISK_MANAGEMENT.md](./RISK_MANAGEMENT.md) - 리스크 관리
