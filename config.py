"""
Configuration and constants for Samsung Auto Trader.
"""

# API Configuration
IS_VIRTUAL = True  # True: 모의투자, False: 실전투자

KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"  # 실전 거래
KIS_VIRTUAL_BASE_URL = "https://openapivts.koreainvestment.com:29443"  # 모의 거래 (올바른 URL/포트)

BASE_URL = KIS_VIRTUAL_BASE_URL if IS_VIRTUAL else KIS_BASE_URL

AUTH_ENDPOINT = "/oauth2/tokenP"
PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-price"
HOLDINGS_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-balance"
BUY_ORDER_ENDPOINT = "/uapi/domestic-stock/v1/trading/order-cash"
SELL_ORDER_ENDPOINT = "/uapi/domestic-stock/v1/trading/order-cash"
ORDER_STATUS_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

# TR IDs
TR_IDS = {
    "PRICE": "FHKST01010100",
    "HOLDINGS": "VTTC8434R" if IS_VIRTUAL else "TTTC8434R",
    "BUY": "VTTC0802U" if IS_VIRTUAL else "TTTC0802U",
    "SELL": "VTTC0801U" if IS_VIRTUAL else "TTTC0801U",
    "ORDER_STATUS": "VTTC8001R" if IS_VIRTUAL else "TTTC8001R",
}

# Trading Configuration
TARGET_STOCK = "005930"  # Samsung Electronics
BUY_OFFSET = 2000  # Buy at current_price - 2000 KRW
SELL_OFFSET = 2000  # Sell at current_price + 2000 KRW
DEFAULT_ORDER_QUANTITY = 1  # Number of shares per order
USE_CURRENT_PRICE_FOR_TEST = False  # 기본 거래 전략 사용

# Trading Window (in 24-hour format)
TRADING_START_HOUR = 9
TRADING_START_MINUTE = 10
TRADING_END_HOUR = 15
TRADING_END_MINUTE = 30

# Polling Configuration
POLLING_INTERVAL_SECONDS = 30  # Check price and balance every 30 seconds
ERROR_RETRY_INTERVAL_SECONDS = 60  # Wait 60 seconds before retrying after error
MAX_RETRIES = 3  # Maximum number of retries for failed API calls

# Token Cache
TOKEN_CACHE_FILE = "token_cache.json"
TOKEN_CACHE_EXPIRY_MINUTES = 600  # Token valid for ~10 hours, cache for 600 minutes

# API Headers Template
COMMON_HEADERS = {
    "Content-Type": "application/json",
}

# HTTP Configuration
REQUEST_TIMEOUT_SECONDS = 10
VERIFY_SSL = True
