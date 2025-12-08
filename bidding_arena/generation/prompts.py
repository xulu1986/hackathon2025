from ..core.constants import StrategyType

class PromptBuilder:
    @staticmethod
    def build(strategy_type: StrategyType) -> str:
        base_prompt = """
You are an expert in RTB (Real-Time Bidding) algorithms.
Your goal is to write a Python function `bidding_strategy` that determines the bid price (CPM) for an ad request.

### Function Signature
```python
import math

def bidding_strategy(
    initial_budget: float,           # Initial budget (USD)
    total_duration: int,             # Total duration (seconds)
    remaining_budget: float,         # Remaining budget
    remaining_time: int,             # Remaining time (seconds)
    winner_price_percentiles: dict,  # {10: p10, ..., 50: median, ..., 90: p90} (CPM)
    conversion_rate: float           # Historical conversion rate (0.0 to 1.0)
) -> float:                          # Return bid price (CPM, USD)
```

### Constraints
1.  **Output**: ONLY the Python code. No markdown formatting, no explanations.
2.  **Libraries**: Use ONLY `math`. No `numpy`, `pandas`, etc.
3.  **Performance**: Must run in < 1ms. Avoid loops if possible.
4.  **Safety**: Bid must be >= 0.

### Strategy Requirements
"""
        
        specific_instructions = {
            StrategyType.IMPRESSION_FOCUSED: """
**Type: Impression-Focused**
- **Goal**: Maximize the number of won auctions (impressions).
- **Tactic**: Bid around the 40th-60th percentile of historical winner prices.
- **Budget**: Spend budget evenly over the remaining time.
""",
            StrategyType.CONVERSION_FOCUSED: """
**Type: Conversion-Focused**
- **Goal**: Maximize total conversions.
- **Tactic**: Bid aggressively (e.g., 70-80th percentile) ONLY when `conversion_rate` is high relative to average.
- **Budget**: Conserve budget for high-value opportunities.
""",
            StrategyType.AGGRESSIVE: """
**Type: Aggressive**
- **Goal**: Spend budget quickly and win high-value inventory.
- **Tactic**: Bid high (e.g., 80-90th percentile).
- **Budget**: Front-load spending. If time is running out, increase bids further.
""",
            StrategyType.CONSERVATIVE: """
**Type: Conservative**
- **Goal**: Minimize CPA (Cost Per Action) and strictly control ROI.
- **Tactic**: Bid low (e.g., < 50th percentile). Only bid if `conversion_rate` is very promising.
- **Budget**: Keep a safety buffer. It's okay to under-spend.
""",
            StrategyType.ADAPTIVE: """
**Type: Adaptive**
- **Goal**: Dynamically adjust based on remaining resources.
- **Tactic**: Start conservative. If `remaining_budget` is high relative to `remaining_time`, become aggressive.
""",
            StrategyType.HYBRID: """
**Type: Hybrid**
- **Goal**: Balance volume and efficiency.
- **Tactic**: Use a weighted score of `conversion_rate` and price percentiles.
"""
        }

        return base_prompt + specific_instructions.get(strategy_type, "") + "\n\nRETURN ONLY THE CODE."

