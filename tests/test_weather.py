"""Offline regression tests: do not contact weather services or the laptop."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("weather", Path(__file__).resolve().parents[1] / "scripts/update-weather.py")
weather = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weather)


class WeatherTests(unittest.TestCase):
    NOW = 1791790200

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.config = root / "weather.json"
        self.config.write_text('{"latitude":-23.13705,"longitude":-64.32426,"temperature_unit":"celsius"}')
        self.cache = root / "cache"
        self.record = {"temperature": 14.9, "code": 0, "is_day": 0,
                       "observed_at": self.NOW, "fetched_at": self.NOW}

    def response(self, unit="°C", temperature=14.9):
        return io.BytesIO(json.dumps({
            "current_units": {"temperature_2m": unit},
            "current": {"temperature_2m": temperature, "weather_code": 0,
                        "is_day": 0, "time": self.NOW},
        }).encode())

    def test_fresh_icon_and_celsius_without_city(self):
        with patch.object(weather, "urlopen", return_value=self.response()) as call:
            self.assertEqual(weather.refresh(self.config, self.cache, self.NOW), 0)
        self.assertEqual((self.cache / "weather.txt").read_text(), "☾ 15°C\n")
        self.assertEqual(call.call_args.kwargs["timeout"], 20)
        self.assertIn("temperature_unit=celsius", call.call_args.args[0].full_url)
        self.assertFalse(list(self.cache.glob(".weather-*")))

    def test_failure_without_cache_is_unavailable(self):
        with patch.object(weather, "urlopen", side_effect=OSError("offline")):
            self.assertEqual(weather.refresh(self.config, self.cache, self.NOW), 1)
        self.assertEqual((self.cache / "weather.txt").read_text(), "☁ --°C\n")

    def test_failure_marks_recent_cache(self):
        self.cache.mkdir()
        (self.cache / "weather-state.json").write_text(json.dumps(self.record))
        with patch.object(weather, "urlopen", side_effect=OSError("offline")):
            weather.refresh(self.config, self.cache, self.NOW + 3600)
        self.assertEqual((self.cache / "weather.txt").read_text(), "~☾ 15°C\n")

    def test_expired_cache_is_not_presented_as_current(self):
        self.cache.mkdir()
        (self.cache / "weather-state.json").write_text(json.dumps(self.record))
        with patch.object(weather, "urlopen", side_effect=OSError("offline")):
            weather.refresh(self.config, self.cache, self.NOW + weather.MAX_AGE + 1)
        self.assertEqual((self.cache / "weather.txt").read_text(), "☁ --°C\n")

    def test_wrong_unit_and_nonfinite_value_rejected(self):
        for response in (self.response(unit="°F"), self.response(temperature=float("nan"))):
            with patch.object(weather, "urlopen", return_value=response):
                self.assertEqual(weather.refresh(self.config, self.cache, self.NOW), 1)
            self.assertEqual((self.cache / "weather.txt").read_text(), "☁ --°C\n")

    def test_clock_rollback_rejects_future_cache(self):
        with self.assertRaises(ValueError):
            weather.valid_record(self.record, self.NOW - 3600)

    def test_condition_icons(self):
        self.assertEqual(weather.weather_icon(0, 1), "☀")
        self.assertEqual(weather.weather_icon(2, 1), "☁")
        self.assertEqual(weather.weather_icon(63, 1), "☂")
        self.assertEqual(weather.weather_icon(71, 1), "❄")
        self.assertEqual(weather.weather_icon(95, 1), "ϟ")


if __name__ == "__main__":
    unittest.main()
