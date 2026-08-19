import datetime as dt

import pandas as pd
import streamlit as st

from data.news import get_combined_calendar, get_saved_filter, save_filter, IMPACT_LEVELS, SOURCES
from ui import theme


def _text(value, default: str = "—") -> str:
    """Escapes a feed value for display, falling back for missing/blank
    ones — pandas leaves absent JSON keys as NaN, not None or ''."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value == "":
        return default
    return theme.esc(value)

st.markdown(
    theme.page_header("Economic Calendar", "Scheduled news events from Forex Factory and myfxbook", icon="calendar"),
    unsafe_allow_html=True,
)

WEEK_OPTIONS = {"Last Week": "last_week", "This Week": "this_week", "Next Week": "next_week"}
week_choice = st.segmented_control("Week", list(WEEK_OPTIONS.keys()), default="This Week", label_visibility="collapsed")

saved_sources = get_saved_filter("page_sources", SOURCES)
selected_sources = st.multiselect("Source", SOURCES, default=saved_sources)
save_filter("page_sources", selected_sources)

week_key = WEEK_OPTIONS.get(week_choice or "This Week")
if "MyFXBook" in selected_sources and week_key != "this_week":
    st.caption("myfxbook only publishes a rolling \"this week\" view, so it's left out of Last/Next Week here — Forex Factory still covers those.")

with st.spinner("Loading calendar…"):
    df = get_combined_calendar(week_key, sources=selected_sources)

if df.empty:
    st.markdown(
        """
        <div class="tj-empty">
            <div class="tj-empty-title">Calendar unavailable</div>
            <div>Couldn't reach either calendar source right now — try again in a bit.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

currencies = sorted(df["country"].dropna().unique())
saved_currencies = [c for c in get_saved_filter("page_currencies", currencies) if c in currencies] or currencies
saved_impacts = get_saved_filter("page_impacts", ["High", "Medium", "Low"])

filt_col1, filt_col2 = st.columns(2)
with filt_col1:
    selected_currencies = st.multiselect("Currency", currencies, default=saved_currencies)
with filt_col2:
    selected_impacts = st.multiselect("Impact", IMPACT_LEVELS, default=saved_impacts)

save_filter("page_currencies", selected_currencies)
save_filter("page_impacts", selected_impacts)

filtered = df[df["country"].isin(selected_currencies) & df["impact"].isin(selected_impacts)]

if filtered.empty:
    st.caption("No events match the selected filters.")
    st.stop()

now = dt.datetime.now()

for day, day_df in filtered.groupby(filtered["date"].dt.date):
    with st.container(key=f"card-newsday-{day.isoformat()}"):
        st.markdown(theme.card_header(day.strftime("%A, %B %d")), unsafe_allow_html=True)
        rows_html = []
        for _, ev in day_df.iterrows():
            forecast = _text(ev["forecast"])
            previous = _text(ev["previous"])
            done_html = (
                f'<span title="Already released" style="color:{theme.GOOD}; display:inline-flex;">{theme.icon_svg("check-circle", 13)}</span>'
                if ev["date"] < now else ""
            )
            rows_html.append(
                '<div style="display:flex; align-items:center; gap:12px; padding:8px 0; '
                f'border-top:1px solid {theme.BORDER};">'
                f'<div style="width:16px; flex-shrink:0;">{done_html}</div>'
                f'<div style="width:64px; flex-shrink:0; font-size:0.78rem; color:{theme.TEXT_SECONDARY}; '
                f'font-variant-numeric:tabular-nums;">{ev["date"].strftime("%I:%M %p").lstrip("0")}</div>'
                f'<div style="width:44px; flex-shrink:0;"><span class="tj-tag">{_text(ev["country"], "")}</span></div>'
                f'<div style="width:74px; flex-shrink:0;">{theme.impact_badge(ev["impact"])}</div>'
                f'<div style="flex:1; font-size:0.86rem; color:{theme.TEXT_PRIMARY};">{_text(ev["title"])}'
                f'<span style="color:{theme.TEXT_SECONDARY}; font-size:0.72rem;"> · {_text(ev["source"], "")}</span></div>'
                f'<div style="width:150px; flex-shrink:0; font-size:0.78rem; color:{theme.TEXT_SECONDARY}; text-align:right;">'
                f'Forecast {forecast} · Prev {previous}</div>'
                "</div>"
            )
        st.markdown("".join(rows_html), unsafe_allow_html=True)
