import beelzebub_bot as b

print("=== BEELZEBUB V2 PAPER CYCLE ===")
print("LIVE_ORDERS_ENABLED:", b.LIVE_ORDERS_ENABLED)
print("PAPER_TRADING_ENABLED:", b.PAPER_TRADING_ENABLED)
print("")

if b.LIVE_ORDERS_ENABLED is not False:
    raise RuntimeError("SAFETY STOP: LIVE ORDERS MUST REMAIN DISABLED")

if b.PAPER_TRADING_ENABLED is not True:
    raise RuntimeError("SAFETY STOP: PAPER TRADING MUST BE ENABLED")

b.run_once()

print("")
print("=== PAPER CYCLE COMPLETE ===")
