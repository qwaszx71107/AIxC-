# utils.py
import re
import time
import math
from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

def compute_log_return(p_start, p_now):
    if p_start <= 0 or p_now <= 0:
        return 0.0
    return math.log(p_now / p_start)

def parse_cd_sec(cd_text: str):
    if not cd_text:
        return None
    nums = re.findall(r"\d+", cd_text)
    if not nums:
        return None
    return int(nums[-1])

def parse_price(text: str):
    if not text:
        return None
    t = text.replace(",", "").strip()
    m = re.search(r"[-+]?\d*\.?\d+", t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except:
        return None

def parse_pct(text: str):
    if not text:
        return None
    m = re.search(r"[-+]?\d*\.?\d+", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except:
        return None

def parse_btn_remain_total(btn_text: str):
    if not btn_text:
        return (None, None)
    m = re.search(r"(\d+)\s*/\s*(\d+)", btn_text)
    if not m:
        return (None, None)
    try:
        return (int(m.group(1)), int(m.group(2)))
    except:
        return (None, None)

def safe_text(driver, xpath, retry=3):
    for _ in range(retry):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except StaleElementReferenceException:
            time.sleep(0.03)
        except Exception:
            time.sleep(0.03)
    return ""

def is_valid_price(p: float, min_p: float, max_p: float):
    return (p is not None) and (min_p <= p <= max_p)

def now_hms(ts_sec: int):
    return datetime.fromtimestamp(ts_sec).strftime("%H:%M:%S")


def parse_cooldown_sec(text: str):
    """
    解析： '100 chances in 14:19:13'
    回傳剩餘秒數 (int) 或 None
    """
    if not text:
        return None

    t = text.strip().lower()
    if "chances in" not in t:
        return None

    # 找 hh:mm:ss
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})\s*:\s*(\d{2})", t)
    if not m:
        return None

    h = int(m.group(1))
    mi = int(m.group(2))
    s = int(m.group(3))
    return h * 3600 + mi * 60 + s