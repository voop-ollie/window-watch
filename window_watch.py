#!/usr/bin/env python3
"""
Window Watch — buzz your phone when it's time to close (or reopen) the windows.

Logic: compare outdoor air temp (Open-Meteo) with your indoor temp (myVAILLANT).
- Outdoor >= indoor            -> "close"  (shut windows/doors/blinds to hold the cool)
- Outdoor <= indoor - HYST     -> "open"   (outside is cooler again, let air through)
- in between                   -> hold the previous state (hysteresis, stops flapping)

Sends an ntfy.sh push only when the state *changes*, so you get one buzz to close up
in the morning and one to reopen in the evening — not every 30 minutes.

Config via environment variables (see README):
  LAT, LON                     location (defaults to Tower Hamlets)
  NTFY_TOPIC                   your private ntfy topic (REQUIRED)
  VAILLANT_USER, VAILLANT_PASS myVAILLANT login (omit to use INDOOR_FALLBACK)
  VAILLANT_BRAND               default "vaillant"
  VAILLANT_COUNTRY             default "unitedkingdom"
  INDOOR_FALLBACK              indoor °C to use if Vaillant is unset/unreachable
  HYSTERESIS                   °C band, default 1.5
  STATE_FILE                   path to persist last state, default ./state.json
"""

import asyncio
import json
import os
import sys
import urllib.parse
import urllib.request

LAT = os.getenv("LAT", "51.5128")
LON = os.getenv("LON", "-0.0566")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")
HYST = float(os.getenv("HYSTERESIS", "1.5"))
STATE_FILE = os.getenv("STATE_FILE", "state.json")
INDOOR_FALLBACK = os.getenv("INDOOR_FALLBACK")


def get_outdoor():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&current=temperature_2m&temperature_unit=celsius"
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    return float(data["current"]["temperature_2m"])


async def get_indoor_vaillant():
    """Read current room temperature from the first myVAILLANT zone."""
    user = os.getenv("VAILLANT_USER")
    pw = os.getenv("VAILLANT_PASS")
    if not (user and pw):
        return None
    from myPyllant.api import MyPyllantAPI

    brand = os.getenv("VAILLANT_BRAND", "vaillant")
    country = os.getenv("VAILLANT_COUNTRY", "unitedkingdom")
    async with MyPyllantAPI(user, pw, brand, country) as api:
        async for system in api.get_systems():
            for zone in getattr(system, "zones", []):
                # primary attribute name in the myPyllant data model
                t = getattr(zone, "current_room_temperature", None)
                if t is not None:
                    return float(t)
                # defensive fallback: scan for any room-temp-like attribute
                for attr in dir(zone):
                    if "room_temperature" in attr and "current" in attr:
                        v = getattr(zone, attr, None)
                        if isinstance(v, (int, float)):
                            return float(v)
    return None


def get_indoor():
    indoor = None
    try:
        indoor = asyncio.run(get_indoor_vaillant())
    except Exception as e:
        print(f"[warn] Vaillant read failed: {e}", file=sys.stderr)
    if indoor is None and INDOOR_FALLBACK:
        indoor = float(INDOOR_FALLBACK)
    return indoor


def decide(outdoor, indoor, last):
    if outdoor >= indoor:
        return "close"
    if outdoor <= indoor - HYST:
        return "open"
    return last or "open"  # inside the band: hold previous


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f).get("status")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(status):
    with open(STATE_FILE, "w") as f:
        json.dump({"status": status}, f)


def notify(title, body, tags, priority="default"):
    if not NTFY_TOPIC:
        print("[error] NTFY_TOPIC not set — cannot send push", file=sys.stderr)
        return
    url = f"{NTFY_SERVER}/{urllib.parse.quote(NTFY_TOPIC)}"
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", title)
    req.add_header("Tags", tags)
    req.add_header("Priority", priority)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def main():
    if not NTFY_TOPIC:
        sys.exit("Set NTFY_TOPIC (your private ntfy topic name).")

    outdoor = get_outdoor()
    indoor = get_indoor()
    if indoor is None:
        sys.exit("No indoor temperature available (Vaillant unreachable and no INDOOR_FALLBACK).")

    last = load_state()
    status = decide(outdoor, indoor, last)
    print(f"outdoor={outdoor:.1f}  indoor={indoor:.1f}  last={last}  -> {status}")

    if status != last:
        if status == "close":
            notify(
                "Close up now",
                f"Outside {outdoor:.1f}°C is now above inside {indoor:.1f}°C. "
                "Shut windows, doors and sun-side blinds.",
                tags="house,sunny",
                priority="high",
            )
        elif status == "open" and last is not None:
            notify(
                "Open up",
                f"Outside {outdoor:.1f}°C has dropped below inside {indoor:.1f}°C. "
                "Open windows to flush the heat out.",
                tags="house,leaves",
            )
    save_state(status)


if __name__ == "__main__":
    main()
