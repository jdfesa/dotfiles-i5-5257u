#!/usr/bin/python3
"""Fetch public city weather once; i3status reads only the cached text."""
import json
from http.client import HTTPException
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MAX_AGE = 3 * 60 * 60
UNAVAILABLE = "☁ --°C"


def weather_icon(code, is_day):
    if code in (0, 1):
        return "☀" if is_day else "☾"
    if code in (2, 3):
        return "☁"
    if code in (45, 48):
        return "≋"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "☂"
    if code in (71, 73, 75, 77, 85, 86):
        return "❄"
    if code in (95, 96, 97, 99):
        return "ϟ"
    return "?"


def valid_record(record, now):
    """Reject malformed, implausible, future-clock or expired observations."""
    temperature = record["temperature"]
    code, is_day = record["code"], record["is_day"]
    observed, fetched = record["observed_at"], record["fetched_at"]
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("invalid temperature")
    if not math.isfinite(temperature) or not -90 <= temperature <= 65:
        raise ValueError("invalid temperature")
    if type(code) is not int or not 0 <= code <= 99 or type(is_day) is not int or is_day not in (0, 1):
        raise ValueError("invalid weather condition")
    for stamp in (observed, fetched):
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
            raise ValueError("invalid timestamp")
        age = now - stamp
        if not math.isfinite(age) or not -600 <= age <= MAX_AGE:
            raise ValueError("expired observation")
    return record


def render(record, stale=False):
    marker = "~" if stale else ""
    return f"{marker}{weather_icon(record['code'], record['is_day'])} {record['temperature']:.0f}°C"


def atomic_write(path, content):
    """Readers see either the old complete record or the new complete record."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".weather-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.flush()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def refresh(config, cache, now=None):
    now = time.time() if now is None else now
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    text_path, state_path = cache / "weather.txt", cache / "weather-state.json"
    try:
        location = json.loads(config.read_text(encoding="utf-8"))
        latitude, longitude = float(location["latitude"]), float(location["longitude"])
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("invalid coordinates")
        if location["temperature_unit"] != "celsius":
            raise ValueError("Celsius required")
        query = urlencode({
            "latitude": latitude, "longitude": longitude,
            "current": "temperature_2m,weather_code,is_day",
            "temperature_unit": "celsius", "timeformat": "unixtime", "forecast_days": 1,
        })
        request = Request("https://api.open-meteo.com/v1/forecast?" + query,
                          headers={"User-Agent": "mbp-sway-weather/1.0"})
        with urlopen(request, timeout=20) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("oversized response")
        data = json.loads(raw)
        if data["current_units"]["temperature_2m"] != "°C":
            raise ValueError("unexpected temperature unit")
        current = data["current"]
        record = valid_record({
            "temperature": current["temperature_2m"], "code": current["weather_code"],
            "is_day": current["is_day"], "observed_at": current["time"], "fetched_at": now,
        }, now)
    except (OSError, HTTPException, ValueError, KeyError, TypeError) as error:
        try:
            record = valid_record(json.loads(state_path.read_text(encoding="utf-8")), now)
            text = render(record, stale=True)
        except (OSError, ValueError, KeyError, TypeError):
            text = UNAVAILABLE
        atomic_write(text_path, text + "\n")
        print(f"weather refresh failed ({type(error).__name__}); cached/unavailable indicator used", file=sys.stderr)
        return 1
    atomic_write(state_path, json.dumps(record) + "\n")
    atomic_write(text_path, render(record) + "\n")
    return 0


if __name__ == "__main__":
    home = Path.home()
    sys.exit(refresh(home / ".config/status/weather.json", home / ".cache/mbp-sway"))
