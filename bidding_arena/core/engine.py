import pandas as pd
from typing import Dict, Any, List
from .interfaces import IReplayEngine, IBiddingStrategy, BidRequest, BidResult
from ..data.generator import MockDataGenerator

class ReplayEngine(IReplayEngine):
    """
    Simulates the bidding process against historical data.
    """
    
    def __init__(self, initial_budget: float = 1000.0):
        self.initial_budget = initial_budget

    def run(self, strategy: IBiddingStrategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the simulation.
        
        Args:
            strategy: The strategy to evaluate.
            data: A DataFrame containing 'timestamp', 'winner_price', 'is_conversion', etc.
        """
        
        # Prepare simulation state
        remaining_budget = self.initial_budget
        
        if data.empty:
            return {"error": "No data provided"}

        start_time = data['timestamp'].min()
        end_time = data['timestamp'].max()
        total_duration = end_time - start_time
        if total_duration == 0: total_duration = 1 # Avoid div by zero

        # Metrics
        win_count = 0
        conversion_count = 0
        total_spend = 0.0
        bids_placed = 0
        
        history: List[Dict[str, Any]] = []

        # Pre-calculate global stats for the strategy context (simplified for now)
        # In a real scenario, this might be segmented or moving average.
        # We'll use the whole dataset stats as "historical knowledge" for the strategy
        # to simplify the 'training' phase assumption.
        percentiles = MockDataGenerator.get_percentiles(data)
        conversion_rate = MockDataGenerator.get_conversion_rate(data)

        for index, row in data.iterrows():
            current_time = row['timestamp']
            elapsed = current_time - start_time
            remaining_time = total_duration - elapsed
            
            # Stop if budget exhausted
            if remaining_budget <= 0:
                break

            request = BidRequest(
                initial_budget=self.initial_budget,
                total_duration=int(total_duration),
                remaining_budget=remaining_budget,
                remaining_time=int(remaining_time),
                winner_price_percentiles=percentiles,
                conversion_rate=conversion_rate 
            )

            # Execute Strategy
            bid_price_cpm = strategy.bid(request)
            bids_placed += 1
            
            # CPM to Unit Price (assuming 1 impression)
            # Usually CPM is per 1000, but let's treat bid_price as "price for this impression" 
            # OR standard CPM logic: cost = bid / 1000? 
            # The spec says "winner_price (CPM)". 
            # Let's assume the auction happens in CPM dollars.
            # But the cost is paid for 1 imp. 
            # Standard: cost = price / 1000. 
            # Let's stick to spec "bid (CPM)".
            
            # Auction Logic (Second Price or First Price? Spec implies "bid >= winner_price")
            # We'll assume First Price for simplicity or just "pay winner price" (Second Price).
            # "Winner price" in logs is usually the clearing price.
            # So if bid >= winner_price, we win and pay winner_price.
            
            is_win = bid_price_cpm >= row['winner_price']
            cost = 0.0
            
            if is_win:
                cost = row['winner_price'] / 1000.0 # CPM to single imp cost
                if remaining_budget >= cost:
                    remaining_budget -= cost
                    win_count += 1
                    total_spend += cost
                    if row['is_conversion'] == 1:
                        conversion_count += 1
                else:
                    # Not enough budget to pay
                    is_win = False
                    cost = 0.0

            # Record history periodically (every 100 or so) to save memory
            if index % 50 == 0:
                history.append({
                    "timestamp": current_time,
                    "remaining_budget": remaining_budget,
                    "win_count": win_count,
                    "conversion_count": conversion_count,
                    "total_spend": total_spend
                })

        # Final Metrics
        win_rate = win_count / bids_placed if bids_placed > 0 else 0
        avg_cpm = (total_spend * 1000 / win_count) if win_count > 0 else 0
        avg_cpa = (total_spend / conversion_count) if conversion_count > 0 else 0
        roi = (conversion_count * 10.0 - total_spend) / total_spend if total_spend > 0 else 0 # Assuming $10 value per conversion
        
        return {
            "win_count": win_count,
            "bids_placed": bids_placed,
            "win_rate": win_rate,
            "conversion_count": conversion_count,
            "total_spend": total_spend,
            "remaining_budget": remaining_budget,
            "avg_cpm": avg_cpm,
            "avg_cpa": avg_cpa,
            "roi": roi,
            "history": history
        }

