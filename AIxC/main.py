# main.py
import time
import threading

from lib.state import make_shared
from lib.ws_client import ws_thread
from lib.web_client import selenium_thread

def main():
    shared, lock = make_shared()

    print(f"[MAIN] 開始預測（不平手模式）", flush=True)
    print(f"[MAIN] 主要停止條件：按鈕顯示 1/100 -> 本把 settle 後 STOP", flush=True)
    print(f"[MAIN] 備援停止條件：counted >= 100", flush=True)
    input("[MAIN] 準備完成後，按 Enter / 空白鍵 開始 Selenium 預測...")

    t1 = threading.Thread(target=ws_thread, args=(shared, lock), daemon=True)
    t2 = threading.Thread(target=selenium_thread, args=(shared, lock), daemon=True)
    t1.start()
    t2.start()

    try:
        while True:
            with lock:
                if shared.stop:
                    break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[MAIN] stop", flush=True)
        with lock:
            shared.stop = True
        time.sleep(0.5)

    with lock:
        wins = shared.wins
        losses = shared.losses
        counted = shared.counted
        flats = shared.flats
        br = shared.btn_remain
        bt = shared.btn_total
        stop_reason = shared.stop_reason

    win_rate = (wins / counted * 100.0) if counted > 0 else 0.0

    print(f"\n{'='*60}")
    print("最終統計：")
    print(f"總場數：{counted} 場 (有效={counted}, 平手={flats})")
    print(f"勝場：{wins}")
    print(f"敗場：{losses}")
    print(f"勝率：{win_rate:.2f}%")
    if br is not None and bt is not None:
        print(f"最後讀到的按鈕：{br}/{bt}")
    if stop_reason:
        print(f"停止原因：{stop_reason}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
