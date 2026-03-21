import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from oneliner.skyscanner_parser import (
    Hop,
    LegData,
    ParseError,
    _fmt_time,
    _format_leg,
    _normalize_month,
    _parse_flight_details,
    _url_to_cache_path,
    summarize,
)

# ---------------------------------------------------------------------------
# Minimal HTML fixture
# ---------------------------------------------------------------------------

FIXTURE_HTML = """
<html><body>
  <div>
    <span>Detalhes de voo</span>
    <div>
      <p>Viagem de ida — 30 de março de 2026</p>
      <p>LIS 5:00 AMS 8:55</p>
      <p>AMS 14:00 BOM 2:35</p>
      <p>BOM 10:50 MLE 13:10</p>
    </div>
  </div>
  <div>
    <span>Detalhes de voo</span>
    <div>
      <p>Viagem de volta — 11 de abril de 2026</p>
      <p>MLE 14:10 BOM 17:30</p>
      <p>BOM 4:40 AMS 11:15</p>
      <p>AMS 12:30 LIS 14:35</p>
    </div>
  </div>
</body></html>
"""

FIXTURE_HTML_NO_DATE = """
<html><body>
  <div>
    <span>Detalhes de voo</span>
    <p>LIS 5:00 AMS 8:55</p>
  </div>
  <div>
    <span>Detalhes de voo</span>
    <p>MLE 14:10 BOM 17:30</p>
  </div>
</body></html>
"""

FIXTURE_HTML_MISSING_SECTION = """
<html><body>
  <p>Nothing useful here</p>
</body></html>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFmtTime(unittest.TestCase):
    def test_single_digit_hour(self):
        self.assertEqual(_fmt_time("5:00"), " 5:00")

    def test_double_digit_hour(self):
        self.assertEqual(_fmt_time("14:00"), "14:00")

    def test_zero_padded_minutes(self):
        self.assertEqual(_fmt_time("8:05"), " 8:05")

    def test_midnight(self):
        self.assertEqual(_fmt_time("0:00"), " 0:00")


class TestNormalizeMonth(unittest.TestCase):
    def test_marco(self):
        self.assertEqual(_normalize_month("março"), "marco")

    def test_abril(self):
        self.assertEqual(_normalize_month("abril"), "abril")

    def test_uppercase(self):
        self.assertEqual(_normalize_month("Março"), "marco")

    def test_junho(self):
        self.assertEqual(_normalize_month("junho"), "junho")

    def test_janeiro(self):
        self.assertEqual(_normalize_month("janeiro"), "janeiro")


class TestFormatLeg(unittest.TestCase):
    def _make_3hop_leg(self):
        return LegData(
            date_str="30 marco",
            hops=[
                Hop("LIS", "5:00", "AMS", "8:55"),
                Hop("AMS", "14:00", "BOM", "2:35"),
                Hop("BOM", "10:50", "MLE", "13:10"),
            ],
        )

    def _make_2hop_leg(self):
        return LegData(
            date_str="11 abril",
            hops=[
                Hop("MLE", "14:10", "BOM", "17:30"),
                Hop("BOM", "4:40", "AMS", "11:15"),
            ],
        )

    def test_3hop(self):
        result = _format_leg(self._make_3hop_leg())
        self.assertEqual(
            result,
            "30 marco: LIS  5:00 ->  8:55 AMS | AMS 14:00 ->  2:35 BOM | BOM 10:50 -> 13:10 MLE",
        )

    def test_2hop(self):
        result = _format_leg(self._make_2hop_leg())
        self.assertEqual(
            result,
            "11 abril: MLE 14:10 -> 17:30 BOM | BOM  4:40 -> 11:15 AMS",
        )


class TestUrlToCachePath(unittest.TestCase):
    def test_deterministic(self):
        url = "https://www.skyscanner.net/transport/flights/lis/mle/"
        p1 = _url_to_cache_path(url, Path("/tmp/cache"))
        p2 = _url_to_cache_path(url, Path("/tmp/cache"))
        self.assertEqual(p1, p2)

    def test_unique_per_url(self):
        p1 = _url_to_cache_path("https://example.com/a", Path("/tmp/cache"))
        p2 = _url_to_cache_path("https://example.com/b", Path("/tmp/cache"))
        self.assertNotEqual(p1, p2)

    def test_ends_with_html(self):
        p = _url_to_cache_path("https://example.com/a", Path("/tmp/cache"))
        self.assertTrue(str(p).endswith(".html"))

    def test_digest_length(self):
        p = _url_to_cache_path("https://example.com/a", Path("/tmp/cache"))
        stem = p.stem  # filename without extension
        self.assertEqual(len(stem), 16)


class TestParseFlightDetails(unittest.TestCase):
    def test_missing_section_raises(self):
        with self.assertRaises(ParseError):
            _parse_flight_details(FIXTURE_HTML_MISSING_SECTION)

    def test_parses_two_legs(self):
        legs = _parse_flight_details(FIXTURE_HTML)
        self.assertEqual(len(legs), 2)

    def test_outbound_date(self):
        legs = _parse_flight_details(FIXTURE_HTML)
        self.assertEqual(legs[0].date_str, "30 marco")

    def test_return_date(self):
        legs = _parse_flight_details(FIXTURE_HTML)
        self.assertEqual(legs[1].date_str, "11 abril")

    def test_outbound_hops(self):
        legs = _parse_flight_details(FIXTURE_HTML)
        hops = legs[0].hops
        self.assertGreater(len(hops), 0)
        self.assertEqual(hops[0].dep_airport, "LIS")
        self.assertEqual(hops[0].dep_time, "5:00")

    def test_return_hops(self):
        legs = _parse_flight_details(FIXTURE_HTML)
        hops = legs[1].hops
        self.assertGreater(len(hops), 0)
        self.assertEqual(hops[0].dep_airport, "MLE")


class TestSummarizeWithMock(unittest.TestCase):
    def test_summarize_uses_cache(self):
        url = "https://www.skyscanner.net/fake"
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with patch(
                "oneliner.skyscanner_parser._fetch_rendered_html",
                return_value=FIXTURE_HTML,
            ) as mock_fetch:
                # First call — should fetch
                out1, ret1 = summarize(url, cache_dir)
                self.assertEqual(mock_fetch.call_count, 1)

                # Second call — should use cache, not fetch again
                out2, ret2 = summarize(url, cache_dir)
                self.assertEqual(mock_fetch.call_count, 1)

            self.assertEqual(out1, out2)
            self.assertEqual(ret1, ret2)

    def test_summarize_cache_file_written(self):
        url = "https://www.skyscanner.net/fake2"
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with patch(
                "oneliner.skyscanner_parser._fetch_rendered_html",
                return_value=FIXTURE_HTML,
            ):
                summarize(url, cache_dir)
            cache_files = list(cache_dir.glob("*.html"))
            self.assertEqual(len(cache_files), 1)

    def test_summarize_returns_two_strings(self):
        url = "https://www.skyscanner.net/fake3"
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "oneliner.skyscanner_parser._fetch_rendered_html",
                return_value=FIXTURE_HTML,
            ):
                result = summarize(url, Path(tmpdir))
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], str)
        self.assertIsInstance(result[1], str)


if __name__ == "__main__":
    unittest.main()
