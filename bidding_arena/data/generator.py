import random
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Generator
from ..core.interfaces import IDataGenerator

class MockDataGenerator(IDataGenerator):
    """Generates synthetic bid request data."""

    def __init__(self, start_time: int = 1700000000):
        self.start_time = start_time
        
    def generate_data(self, num_records: int = 1000) -> pd.DataFrame:
        """Generates a DataFrame of synthetic bid logs."""
        
        platforms = ['iOS', 'Android']
        geos = ['US', 'EU', 'APAC']
        placements = ['Banner', 'Video', 'Interstitial']
        
        data = []
        current_time = self.start_time
        
        for _ in range(num_records):
            # Time advances slightly
            current_time += random.randint(1, 5)
            
            geo = random.choices(geos, weights=[0.4, 0.3, 0.3])[0]
            platform = random.choice(platforms)
            placement = random.choice(placements)
            
            # Base price logic
            base_price = 1.0
            if geo == 'US': base_price *= 2.0
            if placement == 'Video': base_price *= 3.0
            if platform == 'iOS': base_price *= 1.2
            
            # Winner price (log-normal distribution)
            winner_price = np.random.lognormal(mean=np.log(base_price), sigma=0.5)
            
            # Conversion probability
            cv_prob = 0.01
            if geo == 'US': cv_prob *= 1.5
            if placement == 'Interstitial': cv_prob *= 2.0
            
            is_conversion = 1 if random.random() < cv_prob else 0
            
            record = {
                'timestamp': current_time,
                'platform': platform,
                'geo': geo,
                'placement_type': placement,
                'winner_price': round(winner_price, 2),
                'is_conversion': is_conversion,
                'segment_id': f"{platform}_{geo}_{placement}"
            }
            data.append(record)
            
        return pd.DataFrame(data)

    def load_data(self, source: str) -> pd.DataFrame:
        # In a real system, this would load from a CSV/DB
        if source == "mock":
            return self.generate_data()
        try:
            return pd.read_csv(source)
        except Exception:
            return self.generate_data()

    @staticmethod
    def get_percentiles(df: pd.DataFrame) -> Dict[int, float]:
        """Calculates price percentiles from a dataframe."""
        if df.empty:
            return {p: 0.0 for p in range(10, 100, 10)}
        
        percentiles = {}
        for p in range(10, 100, 10):
            percentiles[p] = float(np.percentile(df['winner_price'], p))
        return percentiles

    @staticmethod
    def get_conversion_rate(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        return float(df['is_conversion'].mean())

