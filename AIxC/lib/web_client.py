import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .config import *
from .utils import *
from .strategy import *

def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1400,900")
    return webdriver.Chrome(options=options)

def safe_click(driver, xpath: str):
    if not CLICK_BUTTON:
        print(f"[DRY_RUN] 會點擊 {xpath}，但目前 CLICK_BUTTON=False")
        return
    try:
        el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()
        print(f"[WEB] ✅ CLICKED {xpath}", flush=True)
    except Exception as e:
        print(f"[WEB_ERR] 點擊 {xpath} 失敗: {e}", flush=True)

def click_by_prediction(driver, direction: str):
    if direction == "BUY":
        safe_click(driver, X_BUY_BTN)
    elif direction == "SELL":
        safe_click(driver, X_SELL_BTN)

# def check_max_rounds(shared, lock):
#     with lock:
#         counted = shared.counted
#     if counted >= MAX_ROUNDS:
#         with lock:
#             shared.stop = True
#         print(f"\n[MAIN] ✅ 已完成 {MAX_ROUNDS} 把有效預測 -> STOP (backup max rounds)\n", flush=True)
#         return True
#     return False

def selenium_thread(shared, lock):
    driver = make_driver()
    driver.get(AIXC_URL)

    input("[WEB] 請先手動登入完成，然後按 Enter 繼續...")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, X_CD)))
    print("[WEB] ready", flush=True)

    last_cd_text = None

    try:
        while True:
            with lock:
                if shared.stop:
                    break

            cd_text = safe_text(driver, X_CD)
            price_text = safe_text(driver, X_PRICE)
            pct_text = safe_text(driver, AIXC_percentage)

            buy_btn_text  = safe_text(driver, X_BUY_BTN)
            sell_btn_text = safe_text(driver, X_SELL_BTN)
            r1, t1 = parse_btn_remain_total(sell_btn_text)
            r2, t2 = parse_btn_remain_total(buy_btn_text)

            bt_low = (buy_btn_text or "").lower()
            st_low = (sell_btn_text or "").lower()
            if ("chances in" in bt_low) or ("chances in" in st_low):
                msg = buy_btn_text if ("chances in" in bt_low) else sell_btn_text
                print(f"\n[MAIN] ✅ 偵測到次數冷卻訊息 -> STOP: {msg}\n", flush=True)
                with lock:
                    shared.stop = True
                    shared.stop_reason = f"cooldown: {msg}"
                break
                
            remain = r1 if r1 is not None else r2
            total  = t1 if t1 is not None else t2
            with lock:
                if remain is not None and total is not None:
                    shared.btn_remain = remain
                    shared.btn_total = total

            cd_sec = parse_cd_sec(cd_text)
            price = parse_price(price_text)
            pct_val = parse_pct(pct_text)

            with lock:
                shared.last_aixc_pct = pct_val

            if cd_sec is None or price is None or (not is_valid_price(price, MIN_VALID_PRICE, MAX_VALID_PRICE)):
                print(f"[WEB_WARN] bad read cd='{cd_text}' price_text='{price_text}' parsed_price={price}", flush=True)
                time.sleep(POLL_INTERVAL)
                continue

            with lock:
                shared.last_valid_price = price
                shared.last_valid_cd_text = cd_text
                prev_cd = shared.last_cd_sec
                shared.last_cd_sec = cd_sec

            # New Round
            if prev_cd is not None and cd_sec > prev_cd:
                with lock:
                    has_pending = shared.locked and shared.armed and (shared.entry_price is not None)
                    if has_pending:
                        shared.missX += 1
                if has_pending:
                    settle(shared, lock, price, cd_text, EPS_PRICE, FLAT_RESOLVE_MODE, forced=True)

                with lock:
                    last_pct = shared.last_aixc_pct
                    prev_pct = shared.prev_round_pct
                    odir, reason = compute_override_next_dir(last_pct, prev_pct)
                    shared.override_next_dir = odir
                    shared.override_reason = reason
                    shared.prev_round_pct = last_pct

                    shared.round_id += 1
                    shared.rounds += 1
                    rid = shared.round_id
                    shared.current_round_votes = {"BUY": 0, "SELL": 0}
                    shared.current_round_majority = None

                    ov_show = f" | OVERRIDE_NEXT={odir} ({reason})" if odir else ""
                    pct_show = "pct=N/A" if last_pct is None else f"last_pct={last_pct:+.2f}%"

                    br, bt = shared.btn_remain, shared.btn_total
                    btn_show = f" | BTN={br}/{bt}" if (br is not None and bt is not None) else ""

                print(f"\n[WEB] 🟢 New Round #{rid} (CD jumped {prev_cd} -> {cd_sec}) | {pct_show}{ov_show}{btn_show} | {acc_str(shared, lock)}", flush=True)

            # Vote
            with lock:
                locked_now = shared.locked

            if (not locked_now) and (VOTE_CD_END <= cd_sec <= VOTE_CD_START):
                with lock:
                    ws_dir = shared.ws_dir
                if ws_dir is not None:
                    with lock:
                        shared.current_round_votes[ws_dir] += 1
                        v = shared.current_round_votes
                        maj = "BUY" if v["BUY"] > v["SELL"] else "SELL"
                        shared.current_round_majority = maj
                        shared.last_dir = maj

            # Print status
            with lock:
                ws_dir = shared.ws_dir
                ws_sig = shared.ws_sig_pct
                ws_t = shared.ws_t
                ws_m = shared.ws_recv_mono
                locked = shared.locked
                pred_locked = shared.pred_locked
                sig_locked = shared.sig_locked
                armed = shared.armed
                votes = dict(shared.current_round_votes)
                majority = shared.current_round_majority
                odir = shared.override_next_dir
                oreason = shared.override_reason
                lpct = shared.last_aixc_pct
                br, bt = shared.btn_remain, shared.btn_total

            fres = "N/A" if ws_m is None else f"{int((time.monotonic() - ws_m) * 1000)}ms"
            lock_show = f"LOCKED={pred_locked}({(sig_locked or 0.0):+.4f}%)" if locked else "LOCKED=None"
            arm_show = "ARMED=Y" if armed else "ARMED=N"
            pct_show = "pct=N/A" if lpct is None else f"pct={lpct:+.2f}%"
            ov_show = f"OVR_NEXT={odir}" if odir else "OVR_NEXT=None"
            if odir and oreason:
                ov_show += f"({oreason})"
            btn_show = f"BTN={br}/{bt}" if (br is not None and bt is not None) else "BTN=N/A"

            if PRINT_EVERY_LOOP or (cd_text != last_cd_text):
                if majority is None:
                    print(f"[WEB] CD={cd_text} | AIXC={price:.2f} ({pct_show}) | {btn_show} | WS_單筆={ws_dir or 'N/A'} | "
                          f"多數決=(尚未開始) | {ov_show} | {lock_show} {arm_show} | {acc_str(shared, lock)}", flush=True)
                else:
                    print(f"[WEB] CD={cd_text} | AIXC={price:.2f} ({pct_show}) | {btn_show} | WS_單筆={ws_dir}({(ws_sig or 0.0):+.4f}%) "
                          f"多數決={majority}(B:{votes['BUY']}/S:{votes['SELL']}) "
                          f"Fresh={fres} t={ws_t} | {ov_show} | {lock_show} {arm_show} | {acc_str(shared, lock)}", flush=True)
                last_cd_text = cd_text

            # ENTRY
            with lock:
                already_locked = shared.locked
                rid = shared.round_id
                majority = shared.current_round_majority
                ws_sig_now = shared.ws_sig_pct
                last_dir = shared.last_dir
                odir = shared.override_next_dir
                oreason = shared.override_reason

            if (cd_sec <= LOCK_CD) and (not already_locked):
                if majority is None and FALLBACK_TO_LAST_DIR:
                    majority = last_dir
                    ws_sig_now = 0.0

                final_dir = odir if odir in ("BUY", "SELL") else majority
                used_override = (odir in ("BUY", "SELL"))
                if final_dir is not None:
                    with lock:
                        votes_snap = dict(shared.current_round_votes)
                        lock_entry(shared, rid, cd_text, price, final_dir, float(ws_sig_now or 0.0), forced=False)
                        shared.last_dir = final_dir

                        # if shared.btn_remain == 1 and shared.btn_total is not None:
                        #     shared.stop_after_settle = True
                        #     shared.stop_reason = f"button={shared.btn_remain}/{shared.btn_total} (ENTRY)"

                    ov_tag = f" | OVERRIDE({oreason})" if used_override else ""
                    print(f"   [ROUND {rid}] 🎯 ENTRY@{cd_text} price={price:.2f} | "
                          f"LOCKED={final_dir}(B:{votes_snap['BUY']}/S:{votes_snap['SELL']}) sig={(ws_sig_now or 0.0):+.4f}%{ov_tag} | {acc_str(shared, lock)}",
                          flush=True)
                    click_by_prediction(driver, final_dir)

            # FORCE_ENTRY
            with lock:
                already_locked = shared.locked
                rid = shared.round_id
                majority = shared.current_round_majority
                ws_sig_now = shared.ws_sig_pct
                last_dir = shared.last_dir
                odir = shared.override_next_dir
                oreason = shared.override_reason

            if (cd_sec == 0) and (not already_locked):
                with lock:
                    shared.missE += 1

                if majority is None and FALLBACK_TO_LAST_DIR:
                    majority = last_dir
                    ws_sig_now = 0.0

                final_dir = odir if odir in ("BUY", "SELL") else majority
                used_override = (odir in ("BUY", "SELL"))
                if final_dir is not None:
                    with lock:
                        votes_snap = dict(shared.current_round_votes)
                        lock_entry(shared, rid, cd_text, price, final_dir, float(ws_sig_now or 0.0), forced=True)
                        shared.last_dir = final_dir

                        # if shared.btn_remain == 1 and shared.btn_total is not None:
                        #     shared.stop_after_settle = True
                        #     shared.stop_reason = f"button={shared.btn_remain}/{shared.btn_total} (FORCE_ENTRY)"

                    ov_tag = f" | OVERRIDE({oreason})" if used_override else ""
                    print(f"   [ROUND {rid}] ⚠ FORCE_ENTRY@{cd_text} price={price:.2f} | "
                          f"LOCKED={final_dir}(B:{votes_snap['BUY']}/S:{votes_snap['SELL']}) sig={(ws_sig_now or 0.0):+.4f}%{ov_tag} | {acc_str(shared, lock)}",
                          flush=True)
                    click_by_prediction(driver, final_dir)

            # ARM EXIT
            with lock:
                locked_now = shared.locked
                armed_now = shared.armed

            if locked_now and (cd_sec == ARM_EXIT_SEC) and (not armed_now):
                with lock:
                    shared.armed = True
                    shared.armed_at = time.monotonic()
                    shared.armed_price_snapshot = price
                    er = shared.entry_round
                print(f"   [ROUND {er}] ⏳ ARMED@{cd_text} price={price:.2f} (wait price update) | {acc_str(shared, lock)}", flush=True)

            # SETTLE
            with lock:
                armed_now = shared.armed
                armed_at = shared.armed_at
                snap = shared.armed_price_snapshot
                entry_price = shared.entry_price

            if armed_now and snap is not None and entry_price is not None:
                if abs(price - snap) > EPS_PRICE:
                    settle(shared, lock, price, cd_text, EPS_PRICE, FLAT_RESOLVE_MODE, forced=False)
                elif armed_at is not None and (time.monotonic() - armed_at) > MAX_ARMED_SEC:
                    with lock:
                        shared.missX += 1
                    settle(shared, lock, price, cd_text, EPS_PRICE, FLAT_RESOLVE_MODE, forced=True)

            time.sleep(POLL_INTERVAL)

    finally:
        driver.quit()
        print("[WEB] driver closed", flush=True)
