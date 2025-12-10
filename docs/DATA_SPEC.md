# 데이터 명세

## 📋 개요

백테스트 및 전략 연구에 사용되는 데이터 명세입니다.

## 📊 데이터 스펙

### 기본 요구사항

| 항목 | 값 |
|:---|:---|
| 해상도 | 1분봉 (최소) |
| 기간 | 2년 (최대) |
| 거래소 | 업비트, 바이낸스 |

### OHLCV 데이터

```python
@dataclass
class OHLCVData:
    """OHLCV 데이터 스키마"""
    timestamp: datetime      # UTC 기준
    symbol: str              # 'BTC', 'ETH'
    exchange: str            # 'upbit', 'binance'
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float      # 거래대금 (KRW or USDT)
```

### 김프 데이터

```python
@dataclass
class KimpData:
    """김프율 데이터"""
    timestamp: datetime
    symbol: str
    upbit_price: float       # 업비트 가격 (KRW)
    binance_price: float     # 바이낸스 가격 (USDT)
    usd_krw: float           # 환율
    kimp_rate: float         # 김프율 (계산됨)
```

### 펀딩비 데이터

```python
@dataclass
class FundingData:
    """바이낸스 펀딩비 데이터"""
    timestamp: datetime
    symbol: str
    funding_rate: float      # 펀딩비율 (8시간마다)
    next_funding_time: datetime
```

## 🗄️ 데이터 저장

데이터는 `trading-platform-storage` 레포의 Supabase에 저장됩니다.

### 테이블 구조

```sql
-- OHLCV 데이터
CREATE TABLE ohlcv (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    quote_volume DECIMAL(20, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(timestamp, symbol, exchange)
);

-- 인덱스
CREATE INDEX idx_ohlcv_symbol_time ON ohlcv(symbol, timestamp DESC);
CREATE INDEX idx_ohlcv_exchange ON ohlcv(exchange, timestamp DESC);
```

## 📥 데이터 수집

### 업비트 API

```python
import requests

def fetch_upbit_ohlcv(symbol: str, count: int = 200) -> pd.DataFrame:
    """업비트 OHLCV 조회"""
    url = f"https://api.upbit.com/v1/candles/minutes/1"
    params = {
        'market': f'KRW-{symbol}',
        'count': count
    }
    response = requests.get(url, params=params)
    return pd.DataFrame(response.json())
```

### 바이낸스 API

```python
from binance.client import Client

def fetch_binance_ohlcv(symbol: str, interval: str = '1m') -> pd.DataFrame:
    """바이낸스 OHLCV 조회"""
    client = Client()
    klines = client.get_klines(
        symbol=f'{symbol}USDT',
        interval=interval,
        limit=1000
    )
    return pd.DataFrame(klines)
```

### 환율 데이터

```python
def fetch_usd_krw() -> float:
    """USD/KRW 환율 조회"""
    # 한국수출입은행 API 또는 다른 소스
    pass
```

## 📁 파일 포맷

로컬 캐시용 파일 포맷:

```
data/
├── ohlcv/
│   ├── upbit/
│   │   ├── BTC_1m_2023.parquet
│   │   └── BTC_1m_2024.parquet
│   └── binance/
│       ├── BTCUSDT_1m_2023.parquet
│       └── BTCUSDT_1m_2024.parquet
├── kimp/
│   └── BTC_kimp_2023_2024.parquet
└── funding/
    └── BTCUSDT_funding_2023_2024.parquet
```

### Parquet 사용 이유

- 컬럼 기반 압축 (CSV 대비 ~70% 크기 감소)
- 빠른 읽기 속도
- 스키마 내장
- pandas 직접 지원

```python
# 저장
df.to_parquet('data/ohlcv/upbit/BTC_1m_2023.parquet')

# 로드
df = pd.read_parquet('data/ohlcv/upbit/BTC_1m_2023.parquet')
```

## ⚠️ 데이터 품질

### 검증 항목

- [ ] 결측치 확인
- [ ] 중복 제거
- [ ] 타임존 통일 (UTC)
- [ ] 가격 이상치 탐지
- [ ] 거래량 0 처리

### 결측치 처리

```python
def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """OHLCV 데이터 검증"""
    # 중복 제거
    df = df.drop_duplicates(subset=['timestamp'])
    
    # 결측치 처리 (forward fill)
    df = df.fillna(method='ffill')
    
    # 이상치 제거 (전일 대비 50% 이상 변동)
    df['pct_change'] = df['close'].pct_change()
    df = df[df['pct_change'].abs() < 0.5]
    
    return df
```
