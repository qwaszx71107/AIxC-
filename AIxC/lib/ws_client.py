# ws_client.py
import json
import math
import time
import websocket

from .config import *
from .utils import *

def build_ws_url():
    streams = "/".join([s.lower() + "@markPrice@1s" for s in SYMBOLS])
    return f"wss://fstream.binance.com/stream?streams={streams}"

def ws_thread(shared, lock):
    ws_url = build_ws_url()

    def on_open(ws):
        print(">>> [WS] Binance connection active", flush=True)

    def on_message(ws, message):
        with lock:
            if shared.stop:
                try:
                    ws.close()
                except:
                    pass
                return

        msg = json.loads(message)
        data = msg.get("data", {})
        sym = data.get("s")
        if sym not in WEIGHTS:
            return

        try:
            latest_p = float(data.get("p", 0))
            event_ms = int(data.get("E"))
        except Exception:
            return

        event_sec = event_ms // 1000
        event_time_str = now_hms(event_sec)

        with lock:
            shared.latest_prices[sym] = latest_p

            adj_sec = event_sec - ROUND_OFFSET_SEC
            curr_cid = adj_sec // CYCLE_SEC

            if curr_cid != shared.cycle_id:
                shared.cycle_id = curr_cid
                shared.cycle_start_prices = dict(shared.latest_prices)
                print(f"\n[WS] Cycle {curr_cid} Start @ {event_time_str}", flush=True)

            if shared.cycle_start_prices and len(shared.latest_prices) >= 8:
                start_prices = shared.cycle_start_prices
                latest_prices = shared.latest_prices

                base_return = 0.0
                for s in SYMBOLS:
                    if s in start_prices and s in latest_prices:
                        base_return += compute_log_return(start_prices[s], latest_prices[s]) * WEIGHTS[s]

                btc_r = compute_log_return(start_prices.get("BTCUSDT", 0), latest_prices.get("BTCUSDT", 0))
                signal = math.tanh(AMPLIFY * (base_return + BTC_BIAS * btc_r))
                sig_pct = signal * 100.0
                d = "BUY" if sig_pct >= 0 else "SELL"

                shared.ws_sig_pct = sig_pct
                shared.ws_dir = d
                shared.ws_t = event_time_str
                shared.ws_recv_mono = time.monotonic()

                if PRINT_WS_EVERY_TICK:
                    print(f"[WS_TICK] {sym} p={latest_p} dir={d} sig={sig_pct:+.4f}% t={event_time_str}", flush=True)

    ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
    ws.run_forever(reconnect=5)
