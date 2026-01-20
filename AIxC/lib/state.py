# state.py
from dataclasses import dataclass, field
from typing import Dict, Optional
import threading

@dataclass
class SharedState:
    # WS live
    latest_prices: Dict[str, float] = field(default_factory=dict)
    cycle_id: Optional[int] = None
    cycle_start_prices: Optional[Dict[str, float]] = None

    ws_sig_pct: Optional[float] = None
    ws_dir: Optional[str] = None
    ws_t: Optional[str] = None
    ws_recv_mono: Optional[float] = None

    last_dir: str = "BUY"

    # WEB round/cd
    round_id: int = 0
    last_cd_sec: Optional[int] = None

    current_round_votes: Dict[str, int] = field(default_factory=lambda: {"BUY": 0, "SELL": 0})
    current_round_majority: Optional[str] = None

    # Locked order
    locked: bool = False
    entry_round: Optional[int] = None
    entry_price: Optional[float] = None
    entry_cd: Optional[str] = None
    pred_locked: Optional[str] = None
    sig_locked: Optional[float] = None

    # Exit arm + settle
    armed: bool = False
    armed_at: Optional[float] = None
    armed_price_snapshot: Optional[float] = None

    # Last valid web observation
    last_valid_price: Optional[float] = None
    last_valid_cd_text: Optional[str] = None

    # Accuracy stats
    wins: int = 0
    losses: int = 0
    counted: int = 0
    flats: int = 0

    # Counters
    rounds: int = 0
    entries: int = 0
    settles: int = 0
    forceE: int = 0
    forceS: int = 0
    missE: int = 0
    missX: int = 0

    # AIXC percentage override
    last_aixc_pct: Optional[float] = None
    prev_round_pct: Optional[float] = None
    override_next_dir: Optional[str] = None
    override_reason: str = ""

    # button remain/total
    btn_remain: Optional[int] = None
    btn_total: Optional[int] = None
    stop_after_settle: bool = False
    stop_reason: str = ""

    stop: bool = False

def make_shared():
    lock = threading.Lock()
    shared = SharedState()
    return shared, lock
