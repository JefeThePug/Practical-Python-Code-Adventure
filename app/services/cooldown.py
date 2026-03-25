import time

from flask import session

COOL_DOWNS = [30, 60, 180, 300]  # seconds
RESET_THRESHOLD_MS = 60 * 60 * 1000  # 60 minutes


def handle_cooldown(key: str):
    now = int(time.time() * 1000)
    data = session.get(key, {"attempts": 0, "until": 0})
    attempts = data["attempts"]
    last_until = data["until"]

    if last_until > 0 and (now - last_until) > RESET_THRESHOLD_MS:
        attempts = 0
    if last_until > now:
        return False, last_until - now
    index = min(attempts, len(COOL_DOWNS) - 1)
    cooldown_ms = COOL_DOWNS[index] * 1000
    new_until = now + cooldown_ms
    session[key] = {
        "attempts": attempts + 1,
        "until": new_until,
    }

    return True, cooldown_ms
