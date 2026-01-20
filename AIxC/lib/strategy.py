# strategy.py
from typing import Optional, Tuple
import time

def compute_override_next_dir(curr_pct: Optional[float], prev_pct: Optional[float]) -> Tuple[Optional[str], str]:
    if curr_pct is None:
        return (None, "")

    if curr_pct >= 3.0:
        return ("SELL", f"rule1: curr_pct={curr_pct:+.2f}% >= +3% => next SELL")
    if curr_pct <= -3.0:
        return ("BUY", f"rule2: curr_pct={curr_pct:+.2f}% <= -3% => next BUY")

    if prev_pct is not None:
        s = curr_pct + prev_pct
        # 你原本的門檻照抄（含你註解提到的手滑）
        if s >= 4.0:
            return ("SELL", f"rule3: sum2={s:+.2f}% >= +5% => next SELL")
        if s <= 4.0:
            return ("BUY", f"rule4: sum2={s:+.2f}% <= -5% => next BUY")

    return (None, "")

def acc_str(shared, lock):
    with lock:
        wins = shared.wins
        losses = shared.losses
        counted = shared.counted
        flats = shared.flats
        locked = shared.locked
        armed = shared.armed
        rounds = shared.rounds
        entries = shared.entries
        settles = shared.settles
        forceE = shared.forceE
        forceS = shared.forceS
        missE = shared.missE
        missX = shared.missX

    win_rate = (wins / counted) * 100.0 if counted > 0 else 0.0
    return (f"勝率={win_rate:.2f}% ({wins}勝/{losses}敗/{counted}場) 平手={flats} "
            f"| rounds={rounds} entries={entries} settles={settles} "
            f"missE={missE} missX={missX} forceE={forceE} forceS={forceS} "
            f"| locked={locked} armed={armed}")

def clear_order(shared):
    shared.locked = False
    shared.entry_round = None
    shared.entry_price = None
    shared.entry_cd = None
    shared.pred_locked = None
    shared.sig_locked = None
    shared.armed = False
    shared.armed_at = None
    shared.armed_price_snapshot = None

def lock_entry(shared, rid: int, cd_text: str, price: float, ws_dir: str, ws_sig: float, forced: bool):
    shared.locked = True
    shared.entry_round = rid
    shared.entry_price = price
    shared.entry_cd = cd_text
    shared.pred_locked = ws_dir
    shared.sig_locked = ws_sig
    shared.entries += 1
    if forced:
        shared.forceE += 1

def settle(shared, lock, exit_price: float, exit_cd_text: str, eps_price: float, flat_mode: str, forced: bool):
    with lock:
        rid = shared.entry_round
        entry_price = shared.entry_price
        pred = shared.pred_locked
        sig = shared.sig_locked
        entry_cd = shared.entry_cd
        last_dir = shared.last_dir

    if entry_price is None or pred is None:
        return

    diff = exit_price - entry_price
    if diff > eps_price:
        real = "BUY"
    elif diff < -eps_price:
        real = "SELL"
    else:
        real = last_dir if flat_mode == "LAST" else pred

    correct = (pred == real)

    with lock:
        shared.counted += 1
        shared.settles += 1
        if correct:
            shared.wins += 1
        else:
            shared.losses += 1
        if forced:
            shared.forceS += 1
        shared.flats = 0
        clear_order(shared)

    mark = "✅" if correct else "❌"
    fx = "FORCE" if forced else "OK"
    flat_tag = ""
    if abs(diff) <= eps_price:
        flat_tag = f" (NO-FLAT: diff={diff:+.4f} within ±{eps_price})"

    print(f"   [ROUND {rid}] entry@{entry_cd} {entry_price:.2f} -> exit@{exit_cd_text} {exit_price:.2f} | "
          f"預測={pred}({(sig or 0.0):+.4f}%) 實際={real}{flat_tag} {mark} | settle={fx} | "
          f"{acc_str(shared, lock)}",
          flush=True)

    with lock:
        if shared.stop_after_settle:
            shared.stop = True
            reason = shared.stop_reason or "button=1/100"
            print(f"\n[MAIN] ✅ 按鈕顯示最後一把 -> settle 完成，STOP ({reason})\n", flush=True)

    # check_max_rounds_fn()
