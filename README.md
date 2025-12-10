# Trading Platform Research

🔬 백테스트 엔진, 전략 연구, ML 모델 개발

## 📁 프로젝트 구조

```
research/
├── src/
│   ├── strategies/        # 트레이딩 전략
│   │   ├── base.py       # 전략 베이스 클래스
│   │   ├── kimchi/       # 김치프리미엄 전략
│   │   └── arbitrage/    # 차익거래 전략
│   ├── backtesting/      # 백테스트 엔진
│   │   ├── engine.py     # 백테스트 실행기
│   │   ├── metrics.py    # 성과 지표
│   │   └── report.py     # 리포트 생성
│   ├── data/             # 데이터 처리
│   │   ├── loaders.py    # 데이터 로더
│   │   ├── processors.py # 전처리
│   │   └── features.py   # 피처 엔지니어링
│   ├── models/           # ML 모델
│   │   ├── lstm/         # LSTM 모델
│   │   ├── xgboost/      # XGBoost
│   │   └── rl/           # 강화학습
│   └── utils/            # 유틸리티
├── notebooks/            # Jupyter 노트북
│   ├── exploration/      # 데이터 탐색
│   ├── experiments/      # 실험
│   └── reports/          # 분석 리포트
├── tests/                # 테스트
├── configs/              # 설정 파일
└── data/                 # 데이터 (gitignore)
    ├── raw/
    ├── processed/
    └── cache/
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/vsun410/trading-platform-research.git
cd trading-platform-research

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -e ".[dev]"
```

### 2. 백테스트 실행

```python
from src.backtesting import BacktestEngine
from src.strategies.kimchi import KimchiPremiumStrategy

# 전략 초기화
strategy = KimchiPremiumStrategy(
    entry_threshold=4.0,  # 진입: 김프 > 4%
    exit_threshold=2.0,   # 청산: 김프 < 2%
)

# 백테스트 실행
engine = BacktestEngine(
    strategy=strategy,
    start_date="2024-01-01",
    end_date="2024-12-01",
    initial_capital=100_000_000,  # 1억원
)

results = engine.run()
engine.generate_report()
```

### 3. Jupyter 노트북

```bash
# Jupyter 실행
jupyter lab

# 또는 Docker로 실행
docker-compose -f ../infra/docker-compose.yml --profile research up
# → http://localhost:8888
```

## ⚠️ 주의사항: Look-ahead Bias 방지

```python
# ❌ 잘못된 예: 미래 데이터 사용
df['signal'] = df['future_price'] > df['current_price']

# ✅ 올바른 예: 과거 데이터만 사용
df['signal'] = df['price'].shift(1) > df['ma_20'].shift(1)
```

**체크리스트:**
- [ ] 모든 피처는 shift() 적용 확인
- [ ] 테스트셋은 학습에 절대 사용 안 함
- [ ] Walk-forward 분석으로 검증

## 📊 성과 지표

| 지표 | 목표 | 설명 |
|:---|:---|:---|
| Sharpe Ratio | > 1.5 | 위험 대비 수익 |
| Calmar Ratio | > 2.0 | MDD 대비 수익 |
| Max Drawdown | < 15% | 최대 손실폭 |
| Win Rate | > 60% | 승률 |
| Profit Factor | > 1.5 | 총이익/총손실 |

## 🔗 관련 레포지토리

| 레포 | 설명 |
|:---|:---|
| [docs](https://github.com/vsun410/trading-platform-docs) | 아키텍처 문서 |
| [execution](https://github.com/vsun410/trading-platform-execution) | 실거래 엔진 (Private) |
| [infra](https://github.com/vsun410/trading-platform-infra) | 인프라, Docker |

## 📝 라이선스

MIT License
