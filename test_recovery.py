import sys
import copy
import beelzebub_bot as b

CASES = {
    # Existing 6
    "missing_stop_quantity": {
        "stop_amount": None,
        "expected": "Verified protection order is missing quantity.",
    },
    "missing_target_quantity": {
        "target_amount": None,
        "expected": "Verified protection order is missing quantity.",
    },
    "missing_stop_trigger": {
        "stop_trigger": None,
        "expected": "Verified stop-loss is missing trigger price.",
    },
    "missing_target_trigger": {
        "target_trigger": None,
        "expected": "Verified take-profit is missing trigger price.",
    },
    "stop_trigger_mismatch": {
        "stop_trigger": 83800.0,
        "expected": "Verified stop-loss trigger price does not match expected price.",
    },
    "target_trigger_mismatch": {
        "target_trigger": 84450.0,
        "expected": "Verified take-profit trigger price does not match expected price.",
    },

    # New 10
    "stop_quantity_mismatch": {
        "stop_amount": 0.0001,
        "expected": "Verified stop-loss quantity does not match expected quantity.",
    },
    "target_quantity_mismatch": {
        "target_amount": 0.0001,
        "expected": "Verified take-profit quantity does not match expected quantity.",
    },
    "stop_price_mismatch": {
        "stop_trigger": 83800.0,
        "expected": "Verified stop-loss trigger price does not match expected price.",
    },
    "target_price_mismatch": {
        "target_trigger": 84450.0,
        "expected": "Verified take-profit trigger price does not match expected price.",
    },
    "wrong_stop_client_id": {
        "stop_client_id": "WRONG-STOP-CLIENT-ID",
        "expected": "Verified stop-loss client order ID does not match expected entry.",
    },
    "wrong_target_client_id": {
        "target_client_id": "WRONG-TARGET-CLIENT-ID",
        "expected": "Verified take-profit client order ID does not match expected entry.",
    },
    "wrong_stop_status": {
        "stop_status": "closed",
        "expected": "Verified stop-loss is not open.",
    },
    "wrong_target_status": {
        "target_status": "closed",
        "expected": "Verified take-profit is not open.",
    },
    "wrong_stop_type": {
        "stop_type": "market",
        "expected": "Verified stop-loss has unexpected order type.",
    },
    "wrong_target_type": {
        "target_type": "market",
        "expected": "Verified take-profit has unexpected order type.",
    },
}


def run_case(name):
    case = CASES[name]

    state = {
        "active": True,
        "side": "LONG",
        "entry": 84050.0,
        "stop": 83900.0,
        "target": 84350.0,
        "amount": 0.0002,
        "entry_order_id": f"ENTRY-{name}",
        "stop_order_id": f"STOP-{name}",
        "target_order_id": f"TARGET-{name}",
        "protection_pending": False,
        "live_mode": True,
    }

    original_state = copy.deepcopy(state)

    calls = {
        "verify": 0,
        "save": 0,
    }

    def fake_save(current_state):
        calls["save"] += 1

    def fake_verify(order_id):
        calls["verify"] += 1

        if order_id == state["entry_order_id"]:
            return {
                "id": order_id,
                "symbol": b.SYMBOL,
                "side": "buy",
                "type": "limit",
                "status": "closed",
                "filled": state["amount"],
                "average": state["entry"],
            }

        if order_id == state["stop_order_id"]:
            stop_client_id = case.get(
                "stop_client_id",
                b.protection_client_id(
                    "S",
                    state["entry_order_id"]
                )
            )

            return {
                "id": order_id,
                "symbol": b.SYMBOL,
                "client_order_id": stop_client_id,
                "side": "sell",
                "type": case.get(
                    "stop_type",
                    "stop-loss"
                ),
                "status": case.get(
                    "stop_status",
                    "open"
                ),
                "amount": case.get(
                    "stop_amount",
                    state["amount"]
                ),
                "stop_loss_price": case.get(
                    "stop_trigger",
                    state["stop"]
                ),
                "trigger_price": case.get(
                    "stop_trigger",
                    state["stop"]
                ),
            }

        if order_id == state["target_order_id"]:
            target_client_id = case.get(
                "target_client_id",
                b.protection_client_id(
                    "T",
                    state["entry_order_id"]
                )
            )

            return {
                "id": order_id,
                "symbol": b.SYMBOL,
                "client_order_id": target_client_id,
                "side": "sell",
                "type": case.get(
                    "target_type",
                    "take-profit"
                ),
                "status": case.get(
                    "target_status",
                    "open"
                ),
                "amount": case.get(
                    "target_amount",
                    state["amount"]
                ),
                "take_profit_price": case.get(
                    "target_trigger",
                    state["target"]
                ),
                "trigger_price": case.get(
                    "target_trigger",
                    state["target"]
                ),
            }

        raise RuntimeError("Unexpected order ID.")

    original_save = b.save_state
    original_verify = b.verify_live_order

    b.save_state = fake_save
    b.verify_live_order = fake_verify

    try:
        result = b.recover_live_position(state)

        assert result["status"] == "RECOVERY_HALTED", (
            f"Expected RECOVERY_HALTED, got {result}"
        )

        assert case["expected"] in result["reason"], (
            f"Expected: {case['expected']}\n"
            f"Actual: {result['reason']}"
        )

        assert calls["verify"] == 3, (
            f"Expected 3 verifications, got {calls['verify']}"
        )

        assert calls["save"] == 0, (
            f"Unexpected save count: {calls['save']}"
        )

        assert state == original_state, (
            "State was mutated during failed recovery."
        )

        return True, calls, result["reason"]

    finally:
        b.save_state = original_save
        b.verify_live_order = original_verify


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "all":
        names = list(CASES)
    else:
        names = sys.argv[1:]

    failures = 0

    print("=== BEELZEBUB RECOVERY SAFETY SUITE ===")
    print("REAL ORDERS: DISABLED / MOCKED")
    print("")

    for name in names:
        if name not in CASES:
            print(f"FAIL  {name} -- unknown test")
            failures += 1
            continue

        try:
            passed, calls, reason = run_case(name)

            if passed:
                print(f"PASS  {name}")
                print(f"      {reason}")
                print(
                    f"      VERIFY={calls['verify']} "
                    f"SAVE={calls['save']}"
                )

        except Exception as exc:
            failures += 1
            print(f"FAIL  {name}")
            print(f"      {exc}")

    print("")
    print("======================================")

    if failures == 0:
        print(f"RESULT: ALL {len(names)} TESTS PASSED")
        sys.exit(0)

    print(f"RESULT: {failures} TEST(S) FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()
