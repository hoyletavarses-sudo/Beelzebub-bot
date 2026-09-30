import ccxt
import json
import os
import time
from datetime import datetime, timezone

# =========================
# BEELZEBUB V2 — LONG ONLY
# =========================

BOT_NAME = "BEELZEBUB V2"
SYMBOL = "BTC/USD"
TIMEFRAME = "15m"

# SAFETY
PAPER_TRADING_ENABLED = True
LIVE_ORDERS_ENABLED = False

# RISK
MAX_RISK_USD = 2.00
MAX_POSITION_USD = 25.00
R_MULTIPLE = 2.0

# STRATEGY
SMA_FAST = 20
SMA_SLOW = 50
RSI_PERIOD = 14
RSI_THRESHOLD = 50
VOLUME_PERIOD = 20
VOLUME_MULTIPLIER = 0.90

STATE_FILE = "beelzebub_state.json"

exchange = ccxt.kraken({
    "enableRateLimit": True
})


def load_state():
    default = {
        "active": False,
        "side": None,
        "entry": None,
        "stop": None,
        "target": None,
        "amount": 0.0,
        "entry_time": None,
        "paper_pnl": 0.0,
        "trades": 0,
        "wins": 0,
        "losses": 0
    }

    if not os.path.exists(STATE_FILE):
        return default

    try:
        with open(STATE_FILE, "r") as f:
            saved = json.load(f)

        default.update(saved)
        return default

    except (json.JSONDecodeError, OSError):
        return default


def save_state(state):
    temp_file = STATE_FILE + ".tmp"

    with open(temp_file, "w") as f:
        json.dump(state, f, indent=2)

    os.replace(temp_file, STATE_FILE)


def calculate_rsi(closes, period=14):
    if len(closes) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]

        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            (avg_gain * (period - 1)) + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1)) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100.0 - (100.0 / (1.0 + rs))


def sma(values, period):
    if len(values) < period:
        return None

    return sum(values[-period:]) / period


def get_completed_candles():
    candles = exchange.fetch_ohlcv(
        SYMBOL,
        TIMEFRAME,
        limit=120
    )

    if len(candles) < 60:
        raise RuntimeError(
            "Not enough candle data."
        )

    # Ignore the currently forming candle.
    return candles[:-1]


def position_size(entry, stop):
    risk_distance = abs(entry - stop)

    if risk_distance <= 0:
        return 0.0

    amount_by_risk = (
        MAX_RISK_USD / risk_distance
    )

    amount_by_value = (
        MAX_POSITION_USD / entry
    )

    return min(
        amount_by_risk,
        amount_by_value
    )


def clear_position(state):
    state["active"] = False
    state["side"] = None
    state["entry"] = None
    state["stop"] = None
    state["target"] = None
    state["amount"] = 0.0
    state["entry_time"] = None


def show_paper_position(state, current_price):
    entry = state["entry"]
    stop = state["stop"]
    target = state["target"]
    amount = state["amount"]

    unrealized = (
        current_price - entry
    ) * amount

    print("")
    print("PAPER LONG ACTIVE")
    print(f"Entry: {entry:.2f}")
    print(f"Stop: {stop:.2f}")
    print(f"Target: {target:.2f}")
    print(
        f"Position Size: "
        f"{amount:.8f} BTC"
    )
    print(
        f"Position Value: "
        f"${amount * entry:.2f}"
    )
    print(
        f"Current: {current_price:.2f}"
    )
    print(
        f"Unrealized P/L: "
        f"${unrealized:.4f}"
    )


def manage_paper_position(state, candle):
    if not state["active"]:
        return False

    low = candle[3]
    high = candle[2]
    close = candle[4]

    entry = state["entry"]
    stop = state["stop"]
    target = state["target"]
    amount = state["amount"]

    # If both stop and target are touched
    # during one candle, stop is counted first.
    if low <= stop:

        pnl = (
            stop - entry
        ) * amount

        state["paper_pnl"] += pnl
        state["trades"] += 1
        state["losses"] += 1

        print("")
        print("PAPER LONG STOP HIT")
        print(f"Exit: {stop:.2f}")
        print(f"P/L: ${pnl:.4f}")

        clear_position(state)
        save_state(state)

        return True

    if high >= target:

        pnl = (
            target - entry
        ) * amount

        state["paper_pnl"] += pnl
        state["trades"] += 1
        state["wins"] += 1

        print("")
        print("PAPER LONG TARGET HIT")
        print(f"Exit: {target:.2f}")
        print(f"P/L: ${pnl:.4f}")

        clear_position(state)
        save_state(state)

        return True

    show_paper_position(
        state,
        close
    )

    print("PAPER LONG: HOLD")

    return True


def run_once():
    state = load_state()

    candles = get_completed_candles()

    candle = candles[-1]
    previous = candles[-2]

    timestamp = candle[0]

    candle_time = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    closes = [
        c[4] for c in candles
    ]

    volumes = [
        c[5] for c in candles
    ]

    close = closes[-1]

    sma20 = sma(
        closes,
        SMA_FAST
    )

    sma50 = sma(
        closes,
        SMA_SLOW
    )

    rsi14 = calculate_rsi(
        closes,
        RSI_PERIOD
    )

    typical_prices = [
        (c[2] + c[3] + c[4]) / 3.0
        for c in candles
    ]

    total_volume = sum(volumes)

    vwap = (
        sum(
            tp * vol
            for tp, vol
            in zip(
                typical_prices,
                volumes
            )
        )
        / total_volume
    )

    avg_vol = sma(
        volumes,
        VOLUME_PERIOD
    )

    required_volume = (
        avg_vol * VOLUME_MULTIPLIER
    )

    # =========================
    # BEELZEBUB V2 LONG SETUP
    # =========================

    long_trend = (
        sma20 > sma50
    )

    long_price = (
        close > vwap
    )

    long_rsi = (
        rsi14 > RSI_THRESHOLD
    )

    long_breakout = (
        close > previous[2]
    )

    long_volume = (
        volumes[-1] > required_volume
    )

    long_signal = (
        long_trend
        and long_price
        and long_rsi
        and long_breakout
        and long_volume
    )

    print("")
    print("=" * 55)
    print(
        f"{BOT_NAME} — LONG ONLY PAPER MONITOR"
    )
    print(
        f"{SYMBOL} — 15 MINUTES"
    )
    print("=" * 55)

    print(
        f"Completed Candle: "
        f"{candle_time} UTC"
    )

    print(
        f"Close: {close:.2f}"
    )

    print(
        f"SMA20: {sma20:.2f}"
    )

    print(
        f"SMA50: {sma50:.2f}"
    )

    print(
        f"RSI14: {rsi14:.2f}"
    )

    print(
        f"VWAP: {vwap:.2f}"
    )

    print(
        f"Average Volume(20): "
        f"{avg_vol:.6f}"
    )

    print(
        f"Required Volume: "
        f"{required_volume:.6f}"
    )

    print(
        f"Current Volume: "
        f"{volumes[-1]:.6f}"
    )

    print("")
    print("BEELZEBUB V2 LONG CONDITIONS")

    print(
        f"Trend SMA20 > SMA50: "
        f"{long_trend}"
    )

    print(
        f"Price > VWAP: "
        f"{long_price}"
    )

    print(
        f"RSI > {RSI_THRESHOLD}: "
        f"{long_rsi}"
    )

    print(
        f"Breakout > Previous High: "
        f"{long_breakout}"
    )

    print(
        f"Volume > "
        f"{VOLUME_MULTIPLIER:.1f}x Average: "
        f"{long_volume}"
    )

    # Existing position gets priority.
    if state["active"]:

        manage_paper_position(
            state,
            candle
        )

    elif long_signal:

        entry = close

        # Stop = previous completed
        # candle's low.
        stop = previous[3]

        risk_distance = (
            entry - stop
        )

        if risk_distance <= 0:

            print("")
            print(
                "SIGNAL: LONG BLOCKED"
            )

            print(
                "Previous low is not "
                "below entry."
            )

        else:

            target = (
                entry
                + (risk_distance * R_MULTIPLE)
            )

            amount = position_size(
                entry,
                stop
            )

            if amount <= 0:

                print("")
                print(
                    "SIGNAL: LONG BLOCKED"
                )

                print(
                    "Position size is zero."
                )

            else:

                state["active"] = True
                state["side"] = "LONG"
                state["entry"] = entry
                state["stop"] = stop
                state["target"] = target
                state["amount"] = amount
                state["entry_time"] = (
                    candle_time
                )

                save_state(state)

                print("")
                print(
                    "SIGNAL: LONG"
                )

                print(
                    f"Entry: {entry:.2f}"
                )

                print(
                    f"Stop: {stop:.2f}"
                )

                print(
                    f"Target 2R: "
                    f"{target:.2f}"
                )

                print(
                    f"Position Size: "
                    f"{amount:.8f} BTC"
                )

                print(
                    f"Position Value: "
                    f"${amount * entry:.2f}"
                )

                print(
                    f"Maximum Risk: "
                    f"${MAX_RISK_USD:.2f}"
                )

                print(
                    "PAPER LONG EXECUTED"
                )

                print(
                    "LIVE ORDER: DISABLED"
                )

    else:

        print("")
        print("SIGNAL: WAIT")

        print(
            "No confirmed "
            "BEELZEBUB V2 LONG setup."
        )

        print(
            "WAIT FOR NEXT "
            "15-MINUTE CANDLE"
        )

    print("")
    print(
        f"Paper P/L Total: "
        f"${state['paper_pnl']:.4f}"
    )

    print(
        f"Paper Trades: "
        f"{state['trades']}"
    )

    print(
        f"Wins: "
        f"{state['wins']}"
    )

    print(
        f"Losses: "
        f"{state['losses']}"
    )


def main():

    print("")
    print("=" * 55)
    print("BEELZEBUB V2 BOT STARTED")
    print("=" * 55)

    print(
        "PAPER TRADING: ENABLED"
    )

    print(
        "LIVE ORDERS: DISABLED"
    )

    print(
        f"Market: {SYMBOL}"
    )

    print(
        f"Timeframe: {TIMEFRAME}"
    )

    print(
        "LONG ONLY"
    )

    print(
        f"RSI THRESHOLD: "
        f"{RSI_THRESHOLD}"
    )

    print(
        f"VOLUME THRESHOLD: "
        f"{VOLUME_MULTIPLIER:.1f}x AVERAGE"
    )

    print("")

    last_candle = None

    while True:

        try:

            candles = (
                get_completed_candles()
            )

            completed_timestamp = (
                candles[-1][0]
            )

            if (
                completed_timestamp
                != last_candle
            ):

                last_candle = (
                    completed_timestamp
                )

                run_once()

            else:

                print(
                    f"\rWaiting for next "
                    f"{TIMEFRAME} candle...",
                    end="",
                    flush=True
                )

            time.sleep(20)

        except KeyboardInterrupt:

            print("")
            print(
                "BEELZEBUB V2 STOPPED"
            )

            break

        except Exception as exc:

            print("")
            print(
                f"ERROR: {exc}"
            )

            print(
                "Retrying in 30 seconds..."
            )

            time.sleep(30)


if __name__ == "__main__":
    main()
