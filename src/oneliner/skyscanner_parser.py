from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

MONTHS = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / "tmp" / "cache"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Hop:
    dep_airport: str  # e.g. 'LIS'
    dep_time: str     # e.g. '5:00'
    arr_airport: str  # e.g. 'AMS'
    arr_time: str     # e.g. '8:55'


@dataclass
class LegData:
    date_str: str     # e.g. '30 marco'
    hops: list[Hop]


class SkyscannerError(Exception):
    pass


class FetchError(SkyscannerError):
    pass


class ParseError(SkyscannerError):
    pass


# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------

def _url_to_cache_path(url: str, cache_dir: Path) -> Path:
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.html"


def _load_or_fetch(url: str, cache_dir: Path) -> str:
    path = _url_to_cache_path(url, cache_dir)
    if path.exists():
        return path.read_text(encoding="utf-8")
    html = _fetch_rendered_html(url)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return html


# ---------------------------------------------------------------------------
# Playwright fetch
# ---------------------------------------------------------------------------

def _fetch_rendered_html(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        raise FetchError("Run: uv run playwright install chromium")

    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(headless=True)
            except Exception as e:
                raise FetchError(f"Run: uv run playwright install chromium\n({e})")

            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="pt-PT",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            try:
                page.goto(url, timeout=60_000)
                page.wait_for_load_state("networkidle", timeout=30_000)
                page.wait_for_selector("text=Detalhes de voo", timeout=30_000)
            except PlaywrightTimeout as e:
                raise FetchError(f"Timeout loading page: {e}")
            html = page.content()
            browser.close()
            return html
    except FetchError:
        raise
    except Exception as e:
        raise FetchError(str(e))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_month(m: str) -> str:
    """Strip diacritics and lowercase, e.g. 'Março' → 'marco'."""
    nfd = unicodedata.normalize("NFD", m)
    ascii_bytes = nfd.encode("ascii", "ignore")
    return ascii_bytes.decode("ascii").lower()


def _fmt_time(t: str) -> str:
    """Right-align hour, zero-pad minutes: '5:00' → ' 5:00', '14:00' → '14:00'."""
    h, m = t.split(":")
    return f"{int(h):>2}:{int(m):02d}"


# ---------------------------------------------------------------------------
# HTML Parsing
# ---------------------------------------------------------------------------

def _parse_flight_details(html: str) -> list[LegData]:
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.find_all(string=re.compile(r"Detalhes de voo"))
    if not headings:
        raise ParseError("Could not find 'Detalhes de voo' sections in page")

    legs: list[LegData] = []
    for heading in headings:
        # Walk up to find a container that holds this flight direction's data
        section = heading
        for _ in range(10):
            parent = section.parent
            if parent is None:
                break
            section = parent
            text = section.get_text(" ", strip=True)
            # Stop when we have date and IATA codes in this ancestor
            if re.search(r'\d{1,2}\s+de\s+\w+', text) and re.search(r'[A-Z]{3}', text):
                break

        text = section.get_text(" ", strip=True)

        # Extract date
        date_match = re.search(r'(\d{1,2})\s+de\s+(\w+)', text)
        if not date_match:
            raise ParseError(f"Could not find date in section: {text[:200]}")
        day = date_match.group(1)
        month = _normalize_month(date_match.group(2))
        date_str = f"{day} {month}"

        # Tokenize: IATA codes and times
        tokens = re.findall(r'([A-Z]{3}|\d{1,2}:\d{2})', text)

        # Build hops: expect pattern IATA time IATA time ...
        # We pair tokens as: dep_airport, dep_time, arr_airport, arr_time
        hops: list[Hop] = []
        i = 0
        while i + 3 < len(tokens):
            dep_ap, dep_t, arr_ap, arr_t = tokens[i], tokens[i+1], tokens[i+2], tokens[i+3]
            # Validate pattern: IATA time IATA time
            if (re.fullmatch(r'[A-Z]{3}', dep_ap) and re.fullmatch(r'\d{1,2}:\d{2}', dep_t)
                    and re.fullmatch(r'[A-Z]{3}', arr_ap) and re.fullmatch(r'\d{1,2}:\d{2}', arr_t)):
                hops.append(Hop(dep_ap, dep_t, arr_ap, arr_t))
                i += 2  # next hop starts at arr_ap
            else:
                i += 1

        if not hops:
            raise ParseError(f"Could not parse any hops from section: {text[:200]}")

        legs.append(LegData(date_str=date_str, hops=hops))

    if len(legs) < 2:
        raise ParseError(f"Expected 2 flight directions, found {len(legs)}")

    return legs


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _format_leg(leg: LegData) -> str:
    hop_strs = []
    for hop in leg.hops:
        dep_t = _fmt_time(hop.dep_time)
        arr_t = _fmt_time(hop.arr_time)
        hop_strs.append(f"{hop.dep_airport} {dep_t} -> {arr_t} {hop.arr_airport}")
    return f"{leg.date_str}: {' | '.join(hop_strs)}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize(url: str, cache_dir: Path | None = None) -> tuple[str, str]:
    html = _load_or_fetch(url, cache_dir or DEFAULT_CACHE_DIR)
    legs = _parse_flight_details(html)
    return _format_leg(legs[0]), _format_leg(legs[1])


# ---------------------------------------------------------------------------
# Text-based parsing (clipboard paste)
# ---------------------------------------------------------------------------

def _extract_date(text: str) -> str:
    m = re.search(r"(\d{1,2})/(\d{2})/\d{4}", text)
    if not m:
        raise ValueError(f"No date found in: {text[:100]}")
    day, month = int(m.group(1)), int(m.group(2))
    return f"{day:>2} {MONTHS[month]}"


def _find_time_iata_pairs(text: str) -> list[tuple[str, str]]:
    """Find (time, IATA) pairs where a bare time line is followed by an IATA city line."""
    lines = [l.strip() for l in text.splitlines()]
    pairs = []
    i = 0
    while i < len(lines) - 1:
        if re.fullmatch(r"\d{1,2}:\d{2}", lines[i]):
            j = i + 1
            if j < len(lines) and lines[j] == "+1":
                j += 1
            if j < len(lines) and re.match(r"[A-Z]{3}(\s|$)", lines[j]):
                pairs.append((lines[i], lines[j][:3]))
        i += 1
    return pairs


def _pairs_to_hops(pairs: list[tuple[str, str]]) -> list[str]:
    """Convert flat list of (time, IATA) into hop strings, pairing consecutive entries."""
    hops = []
    for i in range(0, len(pairs) - 1, 2):
        dep_t, dep_ap = pairs[i]
        arr_t, arr_ap = pairs[i + 1]
        hops.append(f"{dep_ap} {_fmt_time(dep_t)} -> {_fmt_time(arr_t)} {arr_ap}")
    return hops


def _extract_cost(text: str) -> str | None:
    pre = text[:text.find("Detalhes de voo")] if "Detalhes de voo" in text else text
    prices_str = re.findall(r"(\d{1,3}(?: \d{3})*) € por pessoa", pre)
    ca_pos = pre.find("Companhia aérea")
    op3_pos = pre.find("Opção 3")
    airline_is_primary = ca_pos != -1 and (op3_pos == -1 or ca_pos < op3_pos)

    if not prices_str:
        # Fallback: "Total de X €." format — pick last price before "Companhia aérea" if present
        search_area = pre[:ca_pos] if ca_pos != -1 else pre
        matches = re.findall(r"(\d{1,3}(?: \d{3})*) €", search_area)
        if not matches:
            return None
        return f"{matches[-1]} €"

    prices = [int(p.replace(" ", "")) for p in prices_str]

    if airline_is_primary:
        m = re.search(r"(\d{1,3}(?: \d{3})*) € por pessoa", pre[ca_pos:])
        airline_price = m.group(1) if m else prices_str[0]
        return f"{airline_price} €"
    else:
        def fmt_price(p: int) -> str:
            s = str(p)
            return f"{s[:-3]} {s[-3:]}" if len(s) > 3 else s
        return f"{fmt_price(min(prices))} € - {fmt_price(max(prices))} €"


def parse_text(text: str) -> list[str]:
    """Parse Skyscanner flight page text (pasted from browser) into summary lines."""
    if "Detalhes de voo" not in text:
        raise ValueError("'Detalhes de voo' not found in text")

    outbound_match = re.search(r"Voo de ida", text)
    return_match = re.search(r"Regresso", text)
    if not outbound_match or not return_match:
        raise ValueError("Could not find 'Voo de ida' or 'Regresso' sections")

    outbound_text = text[outbound_match.start():return_match.start()]
    return_text = text[return_match.start():]

    legs_data = []
    for section in (outbound_text, return_text):
        date_str = _extract_date(section)
        detail_match = re.search(r"^Partida de ", section, re.MULTILINE)
        detail_section = section[detail_match.start():] if detail_match else section
        pairs = _find_time_iata_pairs(detail_section)
        hops = _pairs_to_hops(pairs)
        if not hops:
            raise ValueError(f"No hops found in section starting: {section[:100]}")
        legs_data.append((date_str, hops))

    max_date_len = max(len(d) for d, _ in legs_data)
    lines = [_extract_cost(text) or ""]
    lines += [
        f"{(date_str + ': '):<{max_date_len + 2}}{' | '.join(hops)}"
        for date_str, hops in legs_data
    ]
    return lines
