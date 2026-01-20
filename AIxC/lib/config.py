SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT",
           "TRXUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "HYPEUSDT"]

WEIGHTS = {
    "BTCUSDT": 0.5000, "ETHUSDT": 0.2445, "XRPUSDT": 0.0762, "BNBUSDT": 0.0812,
    "SOLUSDT": 0.0479, "TRXUSDT": 0.0184, "DOGEUSDT": 0.0135, "ADAUSDT": 0.0083,
    "LINKUSDT": 0.0059, "HYPEUSDT": 0.0041,
}

CYCLE_SEC = 13
ROUND_OFFSET_SEC = 9
AMPLIFY = 45.0
BTC_BIAS = 0.15

PRINT_EVERY_LOOP = True
PRINT_WS_EVERY_TICK = False

AIXC_URL = "https://hub.aixcrypto.ai/#prediction-market"

X_PRICE = '//*[@id="root"]/div[1]/div/main/div/div[1]/div/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/span[1]'
X_CD    = '//*[@id="root"]/div[1]/div/main/div/div[1]/div/div[1]/div[2]/div[1]/div[2]/div[2]/div[2]/div/span[1]'
X_BUY_BTN  = '//*[@id="root"]/div/div/main/div/div[1]/div/div[1]/div[2]/div[1]/div[2]/div[1]/div[3]/div'
X_SELL_BTN = '//*[@id="root"]/div/div/main/div/div[1]/div/div[1]/div[2]/div[1]/div[2]/div[2]/div[3]/div'
AIXC_percentage = '//*[@id="root"]/div/div/main/div/div[1]/div/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/span[2]'

POLL_INTERVAL = 0.10

VOTE_CD_START = 10
VOTE_CD_END   = 2
LOCK_CD       = 2

ARM_EXIT_SEC  = 0
MAX_ARMED_SEC = 3.5

MIN_VALID_PRICE = 200.0
MAX_VALID_PRICE = 50000.0

FALLBACK_TO_LAST_DIR = True
MAX_ROUNDS = 100

EPS_PRICE = 0.01
FLAT_RESOLVE_MODE = "PRED"  # "PRED" or "LAST"

CLICK_BUTTON = True


STOP_ON_COOLDOWN = True  
WAIT_ON_COOLDOWN = False 
COOLDOWN_BUFFER_SEC = 3