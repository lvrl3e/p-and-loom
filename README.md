# Trading Journal

A Streamlit app for logging trades and tracking what's actually working:
win rate, risk-reward, equity curve, and performance broken down by
strategy, ticker, month, and day of week.

## Features

- **Log trades**: ticker, direction, entry/exit price, position size,
  entry/exit date, optional stop-loss, strategy tag, notes.
- **Auto-calculated metrics** per trade: P&L ($ and %), holding period,
  R-multiple (when a stop-loss is logged).
- **Aggregate analytics**: win rate, avg win/loss, risk-reward ratio,
  total P&L, max drawdown, and performance by strategy/ticker/month/day
  of week.
- **Visualizations**: equity curve, win/loss distribution, performance by
  strategy bar chart.
- **Journal table** with filters and delete support.

## Project structure

```
Trading-Journal/
├── app.py                  # Home page: quick summary + nav
├── pages/
│   ├── 1_➕_Add_Trade.py    # Trade entry form
│   ├── 2_📒_Journal.py      # Full journal table, filters, delete
│   └── 3_📊_Dashboard.py    # Analytics + charts
├── data/
│   └── db.py                # SQLite data access layer (CRUD)
├── logic/
│   ├── calculations.py      # Per-trade metrics (P&L, R-multiple, ...)
│   └── analytics.py         # Aggregate stats (win rate, drawdown, ...)
├── ui/
│   ├── charts.py             # Plotly figure builders
│   └── format.py             # Display formatting helpers
└── requirements.txt
```

The data layer (`data/db.py`), calculation logic (`logic/`), and UI
(`pages/`, `ui/`) are kept separate so each can evolve independently —
e.g. swapping SQLite for Postgres only means rewriting `data/db.py`.

## Running locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

The app creates `trading_journal.db` (SQLite) in the project root on
first run and persists trades there between sessions.

## Deploying to Streamlit Community Cloud

1. **Push this repo to GitHub** (create a new repo if you haven't yet):

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
   with GitHub.
3. Click **New app**, select this repository/branch, and set the main
   file path to `app.py`.
4. Click **Deploy**. You'll get a shareable URL like
   `https://<app-name>.streamlit.app`.

### Persistence caveat

Streamlit Community Cloud's filesystem is **not durable storage** — the
SQLite file can be wiped on redeploys, app restarts, or reboots of the
underlying container. That's fine for a personal demo, but if you want
your trade history to survive indefinitely:

- Point `TRADING_JOURNAL_DB` (an env var read in `data/db.py`) at a
  mounted volume if your host supports one, **or**
- Swap the SQLite connection in `data/db.py` for a hosted database
  (e.g. Postgres on Supabase/Neon/Railway) using the same function
  signatures — nothing outside `data/db.py` needs to change.

Either way, back up `trading_journal.db` periodically if you're relying
on the free-tier filesystem.

## Data model

Each trade row: `ticker`, `direction` (Long/Short), `entry_price`,
`exit_price`, `position_size`, `stop_loss` (optional), `entry_date`,
`exit_date`, `strategy`, `notes`. A trade is "closed" once it has both
an exit price and exit date — open trades appear in the journal but are
excluded from performance analytics until closed.
