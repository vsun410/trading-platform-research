# 🔬 Research 세부 기획서

**Repository:** trading-platform-research  
**Version:** 1.0  
**Date:** 2025-12-11

---

## 1. 개요

### 1.1 목적

다양한 트레이딩 전략을 연구하고 백테스트하는 환경을 제공합니다. 실거래 환경(order 레포)과 코드를 최대한 공유하여 백테스트 결과와 실제 성과 간의 괴리를 최소화합니다.

### 1.2 핵심 책임

- **전략 개발:** 김프 차익거래, 추세 추종, 평균 회귀 등
- **신호 생성:** 진입/청산 조건 판단 로직
- **백테스트:** 히스토리컬 데이터 기반 시뮬레이션
- **성과 분석:** 수익률, 승률, MDD, Sharpe Ratio 계산

### 1.3 연관 레포지토리

| 레포 | 관계 | 데이터 흐름 |
|------|------|-------------|
| order | 신호 소비자 | research → Signal → order |
| portfolio | 성과 분석 | research → 백테스트 결과 → portfolio |
| storage | 데이터 소스 | storage → 시세 데이터 → research |

---

## 2. 전략 명세

### 2.1 Phase 1: 김프 차익거래 (Cash & Carry)

#### 2.1.1 전략 개요

| 항목 | 내용 |
|------|------|
| 전략명 | 김프 차익거래 (Kimchi Premium Arbitrage) |
| 롱 포지션 | 업비트 BTC/KRW 현물 매수 |
| 숏 포지션 | 바이낸스 BTCUSDT 무기한 선물 매도 |
| 수익원 | ① 김프(프리미엄) 축소 시 차익 ② 펀딩비 수취 |
| 리스크 | 역프 발생, 펀딩비 역전, 거래소 장애 |

#### 2.1.2 김프 계산 공식

```
김프율(%) = (업비트_가격 - 바이낸스_가격 × 환율) / (바이낸스_가격 × 환율) × 100
```

#### 2.1.3 신호 생성 로직

```python
# 진입 조건 (ENTER)
IF 김프율 > ENTRY_THRESHOLD (예: 3.0%)
   AND 펀딩비 > 0 (롱 지불, 숏 수취)
   AND 현재_포지션 == NONE:
       → SIGNAL = ENTER

# 청산 조건 (EXIT)
IF 김프율 < EXIT_THRESHOLD (예: 1.0%)
   OR 펀딩비 < -0.01% (역전)
   OR 김프율 < STOP_LOSS (예: -1.0%):
       → SIGNAL = EXIT
```

#### 2.1.4 전략 파라미터

| 파라미터 | 기본값 | 범위 | 설명 |
|----------|--------|------|------|
| ENTRY_THRESHOLD | 3.0% | 2.0% ~ 5.0% | 진입 김프율 |
| EXIT_THRESHOLD | 1.0% | 0.5% ~ 2.0% | 청산 김프율 |
| STOP_LOSS | -1.0% | -2.0% ~ 0% | 손절 김프율 |
| MIN_FUNDING_RATE | 0.0% | -0.01% ~ 0.05% | 최소 펀딩비 |
| POSITION_SIZE | 50% | 20% ~ 80% | 총 자본 대비 |

### 2.2 Phase 2~4: 추가 전략 (예정)

| Phase | 전략 | 핵심 지표 | 설명 |
|-------|------|-----------|------|
| 2 | 추세 추종 | MA, Breakout | 이동평균 교차, 채널 돌파 |
| 3 | 평균 회귀 | Bollinger, RSI | 과매수/과매도 반전 |
| 4 | 머신러닝 | 예측 모델 | 가격/변동성 예측 기반 |

---

## 3. 백테스트 시스템

### 3.1 백테스트 엔진 구조

```python
class BacktestEngine:
    def __init__(self, strategy, data_loader, config):
        self.strategy = strategy
        self.data_loader = data_loader
        self.simulator = TradeSimulator(config)

    def run(self, start_date, end_date) -> BacktestResult:
        for timestamp, market_data in self.data_loader.iterate():
            signal = self.strategy.generate_signal(market_data)
            self.simulator.execute(signal, market_data)
        return self.simulator.get_result()
```

### 3.2 데이터 요구사항

| 항목 | 요구사항 | 비고 |
|------|----------|------|
| 해상도 | 1분봉 (최소) | 틱 데이터 선택적 |
| 기간 | 최소 1년, 권장 2년 | 다양한 시장 상황 포함 |
| 거래소 | 업비트, 바이낸스 | 동시 타임스탬프 필요 |
| 데이터 종류 | OHLCV, 펀딩비, 환율 | 김프 계산에 필수 |

### 3.3 성과 지표

1. **총 수익률 (Total Return):** (최종자본 - 초기자본) / 초기자본
2. **연환산 수익률 (CAGR):** 연간 복리 수익률
3. **Sharpe Ratio:** (수익률 - 무위험수익률) / 표준편차
4. **MDD (Maximum Drawdown):** 최대 낙폭
5. **승률 (Win Rate):** 수익 거래 / 전체 거래
6. **손익비 (Profit Factor):** 총 이익 / 총 손실

---

## 4. 디렉토리 구조

```
trading-platform-research/
├── README.md                    # 프로젝트 개요
├── pyproject.toml               # 의존성 관리
├── .gitignore
│
├── docs/                        # 문서
│   ├── STRATEGY_GUIDE.md        # 전략 개발 가이드
│   ├── BACKTEST_GUIDE.md        # 백테스트 실행 가이드
│   ├── DATA_SPEC.md             # 데이터 명세
│   └── DETAILED_SPEC.md         # 세부 기획서 (이 문서)
│
├── src/
│   ├── strategies/              # 전략 구현
│   │   ├── __init__.py
│   │   ├── base.py              # BaseStrategy 추상 클래스
│   │   └── kimp/                # 김프 전략
│   │       ├── __init__.py
│   │       ├── calculator.py    # 김프 계산
│   │       └── cash_carry.py    # 전략 로직
│   │
│   ├── backtest/                # 백테스트 엔진
│   │   ├── __init__.py
│   │   ├── engine.py            # BacktestEngine
│   │   ├── simulator.py         # TradeSimulator
│   │   └── metrics.py           # 성과 지표 계산
│   │
│   ├── data/                    # 데이터 처리
│   │   ├── fetcher.py           # 거래소 데이터 수집
│   │   └── preprocessor.py      # 전처리
│   │
│   └── utils/                   # 유틸리티
│       └── logger.py
│
├── strategies/                  # 전략 배포용 (order 레포 공유)
├── notebooks/                   # 연구 노트북
└── tests/                       # 테스트
```

---

## 5. 인터페이스 정의

### 5.1 Signal 데이터 구조

research → order 레포로 전달되는 신호 구조입니다.

```python
@dataclass
class Signal:
    strategy: str          # 전략 식별자 (예: 'kimp_carry')
    action: SignalAction   # ENTER | EXIT | HOLD
    symbol: str            # 대상 심볼 (예: 'BTC')
    confidence: float      # 신뢰도 (0.0 ~ 1.0)
    timestamp: datetime    # 신호 생성 시각
    metadata: dict         # 추가 정보
        # kimp_rate: float    # 현재 김프율
        # funding_rate: float # 현재 펀딩비
        # upbit_price: float  # 업비트 가격
        # binance_price: float # 바이낸스 가격
```

### 5.2 BaseStrategy 인터페이스

```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    @abstractmethod
    def generate_signal(self, market_data: MarketData) -> Signal:
        """시장 데이터를 받아 신호 생성"""
        pass

    @abstractmethod
    def get_parameters(self) -> dict:
        """전략 파라미터 반환"""
        pass
```

---

## 6. 구현 로드맵

| 주차 | 작업 | 산출물 |
|------|------|--------|
| 2주차 | 데이터 수집 & 김프 계산 | 실시간 김프 모니터링 |
| 3주차 | 김프 전략 신호 생성 | Signal 클래스, 진입/청산 로직 |
| 6주차 | 백테스트 시스템 | BacktestEngine, 성과 지표 |

---

*— 문서 끝 —*
