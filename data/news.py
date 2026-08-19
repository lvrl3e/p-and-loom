"""Economic calendar data from two sources, neither of which is an
official API:

- Forex Factory publishes a public weekly JSON feed (nfs.faireconomy.media)
  — the same one many third-party trading tools already rely on instead of
  scraping its markup, so it's far less likely to break silently.
- myfxbook doesn't publish any feed at all, so its calendar is fetched by
  parsing the server-rendered HTML table on its calendar page directly.
  This is inherently more fragile — it breaks if myfxbook changes their
  markup — and only ever returns whichever forward-looking window their
  page defaults to (there's no separate last/this/next-week request like
  Forex Factory's feed has). myfxbook also sits behind a Cloudflare JS
  challenge that blocks plain HTTP clients outright (curl and requests
  both got a consistent 403 in testing, not just occasionally), so the
  fetch launches headless Chromium via Playwright to actually execute the
  challenge — see _fetch_myfxbook_html() for the fallback chain if that
  isn't available. Even so, this source should be treated as best-effort:
  it can still legitimately return nothing (Playwright not installed, the
  browser binary not downloaded, myfxbook tightening its bot detection
  further), which is why get_myfxbook_calendar() never raises — a failed
  fetch just means an empty DataFrame, and the combined calendar quietly
  falls back to Forex Factory alone.
"""

import datetime as dt
import shutil
import subprocess

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

from data.db import get_setting, set_setting

_FF_FEED_URLS = {
    "last_week": "https://nfs.faireconomy.media/ff_calendar_lastweek.json",
    "this_week": "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
    "next_week": "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
}
_MYFXBOOK_URL = "https://www.myfxbook.com/forex-economic-calendar"
_MYFXBOOK_IMPACT_MAP = {"impact_high": "High", "impact_medium": "Medium", "impact_low": "Low", "impact_none": "Low"}

IMPACT_LEVELS = ["High", "Medium", "Low", "Holiday"]
SOURCES = ["Forex Factory", "MyFXBook"]
_COLUMNS = ["date", "country", "impact", "title", "forecast", "previous", "source"]


def _empty_calendar() -> pd.DataFrame:
    """An empty result with 'date' explicitly typed as datetime64 — a bare
    pd.DataFrame(columns=_COLUMNS) leaves it as object dtype, which
    silently downgrades a real fetch's datetime64 'date' column to object
    too once pd.concat mixes the two (breaking any later .dt accessor
    use), so every empty-result path below goes through this instead."""
    df = pd.DataFrame(columns=_COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    return df

# Filter preferences saved to the settings table (see data.db.get/set_setting)
# so re-opening the app doesn't reset them — "page" is the full Economic
# Calendar page, "widget" is the compact Dashboard card, each remembered
# independently since they're different views onto the same feed.
_FILTER_SETTING_KEYS = {
    "page_currencies": "news_page_currencies",
    "page_impacts": "news_page_impacts",
    "page_sources": "news_page_sources",
    "widget_currencies": "news_widget_currencies",
    "widget_impacts": "news_widget_impacts",
    "widget_sources": "news_widget_sources",
}


def get_saved_filter(name: str, default: list[str]) -> list[str]:
    raw = get_setting(_FILTER_SETTING_KEYS[name])
    if not raw:
        return default
    return [v for v in raw.split(",") if v]


def save_filter(name: str, values: list[str]) -> None:
    set_setting(_FILTER_SETTING_KEYS[name], ",".join(values))


@st.cache_data(ttl=1800, show_spinner=False)
def get_calendar(week: str = "this_week") -> pd.DataFrame:
    """Fetches and normalizes one week of the Forex Factory calendar feed,
    with event times converted from the feed's timestamps to the local
    machine's timezone. Cached for 30 minutes — this is a scheduled
    calendar, not a live feed, so there's no need to re-fetch on every
    rerun. Returns an empty DataFrame (never raises) if the feed can't be
    reached, so a network hiccup doesn't take down the page it's on."""
    url = _FF_FEED_URLS.get(week, _FF_FEED_URLS["this_week"])
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        raw = resp.json()
    except (requests.RequestException, ValueError):
        return _empty_calendar()

    df = pd.DataFrame(raw)
    if df.empty:
        return _empty_calendar()

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    local_tz = dt.datetime.now().astimezone().tzinfo
    df["date"] = df["date"].dt.tz_convert(local_tz).dt.tz_localize(None)
    df["source"] = "Forex Factory"
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    for col in _COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[_COLUMNS]


def _fetch_myfxbook_html() -> str | None:
    """myfxbook sits behind a Cloudflare JS challenge that blocks plain
    HTTP clients outright — confirmed empirically, curl and requests both
    got a hard 403 "Just a moment..." page in testing, consistently, not
    just occasionally. Only a real browser engine that actually executes
    the challenge's JS gets through, so this launches headless Chromium
    via Playwright first (confirmed working: loads the page for real and
    waits for the calendar table to render). That needs `playwright
    install chromium` to have been run once — if Playwright itself isn't
    installed, or the browser binary hasn't been downloaded, the import
    or launch fails and this falls through to curl, then requests, either
    of which may still occasionally get through on their own."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
                page.goto(_MYFXBOOK_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector("tr.economicCalendarRow", timeout=20000)
                return page.content()
            finally:
                browser.close()
    except Exception:
        # Broad on purpose — Playwright's failure modes here (missing
        # package, missing browser binary, navigation timeout, challenge
        # not clearing in time) all mean the same thing to this function:
        # fall back to the next fetch method rather than surface an error,
        # matching get_myfxbook_calendar()'s "never raises" contract.
        pass

    if shutil.which("curl"):
        try:
            result = subprocess.run(
                ["curl", "-s", "-A", "Mozilla/5.0", "--max-time", "15", _MYFXBOOK_URL],
                capture_output=True, text=True, timeout=20, encoding="utf-8", errors="replace",
            )
            if result.returncode == 0 and "economicCalendarRow" in result.stdout:
                return result.stdout
        except (subprocess.SubprocessError, OSError):
            pass
    try:
        resp = requests.get(_MYFXBOOK_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_myfxbook_calendar() -> pd.DataFrame:
    """Scrapes myfxbook's economic calendar page. Each event row carries an
    explicit Unix-epoch timestamp (in a `time="..."` attribute, UTC) that
    myfxbook's own page uses for its live countdowns — reading that instead
    of the human-readable date text sidesteps any guessing about what
    timezone the page renders in. Returns an empty DataFrame (never
    raises) on any failure, same contract as get_calendar()."""
    html = _fetch_myfxbook_html()
    if not html:
        return _empty_calendar()
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for tr in soup.select("tr.economicCalendarRow"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 6:
            continue
        time_span = tr.select_one("span[time]")
        if not time_span or not time_span.get("time"):
            continue
        try:
            event_dt = dt.datetime.fromtimestamp(int(time_span["time"]) / 1000, tz=dt.timezone.utc)
        except (ValueError, OSError):
            continue
        is_holiday = time_span.get("data-is-holiday") == "true"

        country = tds[3].get_text(strip=True)
        title_el = tds[4].find("a") or tds[4].find("span")
        title = title_el.get_text(strip=True) if title_el else tds[4].get_text(strip=True)

        impact_div = tds[5].find("div")
        impact_class = next((c for c in (impact_div.get("class") or []) if c.startswith("impact_")), "impact_low")
        impact = "Holiday" if is_holiday else _MYFXBOOK_IMPACT_MAP.get(impact_class, "Low")

        previous = tds[6].get_text(strip=True) if len(tds) > 6 else ""
        forecast = tds[7].get_text(strip=True) if len(tds) > 7 else ""

        rows.append({
            "date": event_dt, "country": country, "impact": impact,
            "title": title, "forecast": forecast, "previous": previous, "source": "MyFXBook",
        })

    if not rows:
        return _empty_calendar()

    df = pd.DataFrame(rows)
    local_tz = dt.datetime.now().astimezone().tzinfo
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(local_tz).dt.tz_localize(None)
    return df.sort_values("date").reset_index(drop=True)[_COLUMNS]


def get_combined_calendar(week: str = "this_week", sources: list[str] | None = None) -> pd.DataFrame:
    """Merges both sources, tagged by their "source" column. myfxbook only
    ever returns one rolling window (no separate last/this/next-week
    request like Forex Factory's feed), so it's only included for
    week="this_week" — its full scraped range, unclipped. An earlier
    version clipped it to Forex Factory's own week boundary instead,
    which silently dropped real myfxbook events that fell outside that
    specific window (e.g. weekend events, since Forex Factory's week
    stops at Friday). For "last_week"/"next_week" there's no reliable way
    to know which of myfxbook's events (if any) actually belong to that
    week, so it's left out rather than guessed at."""
    sources = SOURCES if sources is None else sources
    frames = []
    if "Forex Factory" in sources:
        frames.append(get_calendar(week))
    if "MyFXBook" in sources and week == "this_week":
        frames.append(get_myfxbook_calendar())

    if not frames:
        return _empty_calendar()
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return combined
    return combined.sort_values("date").reset_index(drop=True)


def upcoming_events(
    df: pd.DataFrame,
    impacts: list[str] | None = None,
    currencies: list[str] | None = None,
    limit: int = 5,
) -> pd.DataFrame:
    """Events from right now onward, soonest first — used by the Overview
    page's compact widget. impacts/currencies=None means no filtering on
    that field."""
    if df.empty:
        return df
    upcoming = df[df["date"] >= dt.datetime.now()]
    if impacts is not None:
        upcoming = upcoming[upcoming["impact"].isin(impacts)]
    if currencies is not None:
        upcoming = upcoming[upcoming["country"].isin(currencies)]
    return upcoming.head(limit)
