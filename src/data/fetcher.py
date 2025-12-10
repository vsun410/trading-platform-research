"""데이터 수집기"""

from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import httpx
from loguru import logger


class DataFetcher:
    """
    거래소 데이터 수집기
    
    지원 거래소:
    - 업비트 (KRW 마켓)
    - 바이낸스 (USDT 마켓, 선물)
    
    Example:
        >>> fetcher = DataFetcher()
        >>> df = fetcher.get_upbit_ohlcv('BTC', days=30)
    """
    
    def __init__(self):
        self.client = httpx.Client(timeout=30)
        
    def get_upbit_ohlcv(
        self, 
        symbol: str, 
        interval: str = 'minute1',
        count: int = 200,
        to: Optional[str] = None
    ) -> pd.DataFrame:
        """
        업비트 OHLCV 조회
        
        Args:
            symbol: 심볼 (예: 'BTC')
            interval: 'minute1', 'minute5', 'minute15', 'minute60', 'day'
            count: 조회 개수 (최대 200)
            to: 기준 시간 (ISO format)
            
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume]
        """
        interval_map = {
            'minute1': 'minutes/1',
            'minute5': 'minutes/5',
            'minute15': 'minutes/15',
            'minute60': 'minutes/60',
            'day': 'days'
        }
        
        url = f"https://api.upbit.com/v1/candles/{interval_map.get(interval, 'minutes/1')}"
        params = {
            'market': f'KRW-{symbol}',
            'count': min(count, 200)
        }
        if to:
            params['to'] = to
            
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'candle_date_time_utc': 'timestamp',
                'opening_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'trade_price': 'close',
                'candle_acc_trade_volume': 'volume'
            })
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('timestamp').reset_index(drop=True)
            df['exchange'] = 'upbit'
            df['symbol'] = symbol
            
            return df
            
        except Exception as e:
            logger.error(f"업비트 데이터 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_binance_ohlcv(
        self,
        symbol: str,
        interval: str = '1m',
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        futures: bool = False
    ) -> pd.DataFrame:
        """
        바이낸스 OHLCV 조회
        
        Args:
            symbol: 심볼 (예: 'BTC')
            interval: '1m', '5m', '15m', '1h', '1d'
            limit: 조회 개수 (최대 1000)
            start_time: 시작 시간 (ms timestamp)
            end_time: 종료 시간 (ms timestamp)
            futures: 선물 여부
            
        Returns:
            DataFrame
        """
        if futures:
            url = "https://fapi.binance.com/fapi/v1/klines"
        else:
            url = "https://api.binance.com/api/v3/klines"
            
        params = {
            'symbol': f'{symbol}USDT',
            'interval': interval,
            'limit': min(limit, 1000)
        }
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['exchange'] = 'binance_futures' if futures else 'binance'
            df['symbol'] = symbol
            
            return df
            
        except Exception as e:
            logger.error(f"바이낸스 데이터 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_binance_funding_rate(
        self,
        symbol: str,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        바이낸스 펀딩비 조회
        
        Args:
            symbol: 심볼 (예: 'BTC')
            limit: 조회 개수
            
        Returns:
            DataFrame
        """
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {
            'symbol': f'{symbol}USDT',
            'limit': limit
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data)
            df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
            df['fundingRate'] = df['fundingRate'].astype(float)
            df = df.rename(columns={
                'fundingTime': 'timestamp',
                'fundingRate': 'funding_rate'
            })
            
            return df[['timestamp', 'symbol', 'funding_rate']]
            
        except Exception as e:
            logger.error(f"펀딩비 조회 실패: {e}")
            return pd.DataFrame()
    
    def close(self):
        """클라이언트 종료"""
        self.client.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
