"""전략 테스트"""

import pytest
import pandas as pd
from datetime import datetime

from src.strategies.kimp.cash_carry import KimpCashCarryStrategy


class TestKimpCashCarryStrategy:
    """김프 차익거래 전략 테스트"""
    
    def test_init_default_params(self):
        """기본 파라미터 테스트"""
        strategy = KimpCashCarryStrategy({})
        
        assert strategy.entry_threshold == 0.03
        assert strategy.exit_threshold == 0.01
        assert strategy.position_size == 1.0
        
    def test_init_custom_params(self):
        """커스텀 파라미터 테스트"""
        params = {
            'entry_threshold': 0.05,
            'exit_threshold': 0.02,
            'position_size': 0.5
        }
        strategy = KimpCashCarryStrategy(params)
        
        assert strategy.entry_threshold == 0.05
        assert strategy.exit_threshold == 0.02
        assert strategy.position_size == 0.5
        
    def test_invalid_params(self):
        """잘못된 파라미터 테스트"""
        # entry <= exit
        with pytest.raises(ValueError):
            KimpCashCarryStrategy({
                'entry_threshold': 0.01,
                'exit_threshold': 0.03
            })
            
    def test_calculate_kimp(self):
        """김프율 계산 테스트"""
        strategy = KimpCashCarryStrategy({})
        
        # 김프 0%
        kimp = strategy.calculate_kimp(
            upbit_price=130_000_000,
            binance_price=100_000,
            usd_krw=1_300
        )
        assert kimp == pytest.approx(0.0, abs=0.001)
        
        # 김프 5%
        kimp = strategy.calculate_kimp(
            upbit_price=136_500_000,
            binance_price=100_000,
            usd_krw=1_300
        )
        assert kimp == pytest.approx(0.05, abs=0.001)
        
        # 역프 -3%
        kimp = strategy.calculate_kimp(
            upbit_price=126_100_000,
            binance_price=100_000,
            usd_krw=1_300
        )
        assert kimp == pytest.approx(-0.03, abs=0.001)
        
    def test_generate_signal_entry(self):
        """진입 시그널 테스트"""
        strategy = KimpCashCarryStrategy({'entry_threshold': 0.03})
        
        # 김프 5% → 진입
        data = pd.DataFrame([{
            'timestamp': datetime.now(),
            'upbit_price': 136_500_000,
            'binance_price': 100_000,
            'usd_krw': 1_300
        }])
        
        signal = strategy.generate_signal(data)
        
        assert signal is not None
        assert signal.action == 'BUY'
        assert signal.metadata['type'] == 'ENTRY'
        assert strategy.is_in_position == True
        
    def test_generate_signal_no_entry(self):
        """진입 조건 미충족 테스트"""
        strategy = KimpCashCarryStrategy({'entry_threshold': 0.05})
        
        # 김프 3% → 진입 안함 (threshold: 5%)
        data = pd.DataFrame([{
            'timestamp': datetime.now(),
            'upbit_price': 133_900_000,
            'binance_price': 100_000,
            'usd_krw': 1_300
        }])
        
        signal = strategy.generate_signal(data)
        
        assert signal is None
        assert strategy.is_in_position == False
        
    def test_generate_signal_exit(self):
        """청산 시그널 테스트"""
        strategy = KimpCashCarryStrategy({
            'entry_threshold': 0.03,
            'exit_threshold': 0.01
        })
        strategy.is_in_position = True
        
        # 김프 0.5% → 청산
        data = pd.DataFrame([{
            'timestamp': datetime.now(),
            'upbit_price': 130_650_000,
            'binance_price': 100_000,
            'usd_krw': 1_300
        }])
        
        signal = strategy.generate_signal(data)
        
        assert signal is not None
        assert signal.action == 'SELL'
        assert signal.metadata['type'] == 'EXIT'
        assert strategy.is_in_position == False


class TestPerformanceMetrics:
    """성과 지표 테스트"""
    
    def test_max_drawdown(self):
        """MDD 계산 테스트"""
        from src.backtest.metrics import PerformanceMetrics
        
        # 100 → 120 → 90 → 100
        equity = pd.Series([100, 110, 120, 90, 100])
        equity.index = pd.date_range('2024-01-01', periods=5)
        
        metrics = PerformanceMetrics(equity)
        mdd = metrics.max_drawdown()
        
        # MDD = (120 - 90) / 120 = 25%
        assert mdd == pytest.approx(0.25, abs=0.01)
