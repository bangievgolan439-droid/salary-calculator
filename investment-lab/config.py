"""Approved parameters from PLAN.md Section 10. Change only by re-approving the plan section."""

# --- Risk Manager limits (PLAN.md Section 4) ---
MAX_DAILY_LOSS_PCT = 2.0       # halts new trades for the rest of the day
MAX_POSITION_SIZE_PCT = 10.0   # of account equity, per position
MAX_CONCURRENT_POSITIONS = 3
MIN_CASH_BUFFER_PCT = 30.0     # kept unallocated at all times

# --- Strategy parameters (PLAN.md Section 5a) ---
EMA_FAST = 50
EMA_SLOW = 200
ADX_PERIOD = 14
ADX_TREND_THRESHOLD = 20       # only act on the EMA cross when ADX is above this
TIMEFRAME = "4Hour"            # alpaca-py TimeFrame string

# --- Phase 1 test assets (PLAN.md Section 10, item 4) ---
TEST_STOCK_SYMBOL = "AAPL"
TEST_CRYPTO_SYMBOL = "BTC/USD"

# --- Data plan (PLAN.md Section 5a) ---
DATA_FEED = "iex"  # free Basic plan feed for equities; crypto has no feed parameter
