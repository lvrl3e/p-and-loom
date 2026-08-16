# Trading Journal

A modern **trading performance journal built for prop-firm and funded-account traders**. Track multiple trading accounts, log daily profit and loss, review performance through a calendar, and keep notes and screenshots for every trading day.

![Trading Journal Dashboard](docs/screenshots/dashboard.png)

## ✨ Features

### 🏦 Multiple Trading Accounts

Create and manage multiple accounts with different account sizes.

* Prop-firm accounts
* Funded accounts
* Personal trading accounts
* Different starting balances
* Separate performance tracking per account
* Easily switch between accounts from the dashboard

### 📅 Daily P&L Journal

Instead of recording individual trades, quickly log your **overall result for the day**.

For each date, record:

* Daily profit or loss
* Notes
* Screenshots
* Trading-day observations

Positive, negative, and break-even days are automatically identified.

### 🗓️ Performance Calendar

View your entire trading history through a visual calendar.

Each day displays its performance using visual indicators:

* 🟢 Profit
* 🔴 Loss
* ⚪ Break-even
* Dark/empty days for days without an entry

Click any date to view or edit the day's P&L, notes, and screenshots.

### 📊 Performance Analytics

Automatically calculate performance metrics for each account:

* Current balance
* Total P&L
* P&L percentage
* Winning days
* Losing days
* Break-even days
* Win rate
* Average daily profit
* Average daily loss
* Best day
* Worst day
* Winning streak
* Losing streak
* Maximum drawdown

### 🎯 Prop-Firm Progress

Track important account milestones such as:

* Profit target
* Progress toward target
* Remaining profit needed
* Maximum drawdown
* Current drawdown
* Distance to drawdown limit

This makes it easy to see how close an account is to reaching its target while keeping risk under control.

### 📈 Equity & P&L Charts

Visualize account performance with:

* Cumulative P&L
* Equity curve
* Daily performance
* Drawdown
* Monthly performance

Filter performance by different time periods such as:

`7D · 1M · 3M · 6M · 1Y · All`

### 📝 Daily Notes

Keep a journal for each trading day.

Record things such as:

* Market observations
* Trading psychology
* Mistakes
* Lessons learned
* Strategy observations
* Goals for the next session

### 📸 Trading Screenshots

Attach screenshots to individual journal entries.

Useful for saving:

* TradingView charts
* Trading platform screenshots
* Prop-firm dashboards
* Performance screenshots
* Important market setups

## 🎨 Design

Trading Journal uses a **dark trading-terminal inspired interface** with a modern SaaS aesthetic.

* Dark UI
* Pink accent color
* Green profit indicators
* Red loss indicators
* Minimal cards and borders
* Responsive layouts
* Data-focused visualizations

## 📁 Project Structure

```text
Trading-Journal/
├── app.py
│
├── views/
│   ├── overview.py
│   ├── accounts.py
│   ├── journal.py
│   ├── calendar.py
│   └── analytics.py
│
├── data/
│   └── db.py
│
├── logic/
│   ├── calculations.py
│   └── analytics.py
│
├── ui/
│   ├── theme.py
│   ├── charts.py
│   └── format.py
│
├── docs/
│   └── screenshots/
│       └── dashboard.png
│
├── requirements.txt
└── README.md
```

## 🧮 How It Works

The application is focused on **daily account-level performance rather than individual trade execution**.

A typical workflow is:

```text
Create Account
      ↓
Select Account
      ↓
Select Trading Date
      ↓
Enter Daily P&L
      ↓
Add Notes
      ↓
Upload Screenshots
      ↓
Save Journal Entry
      ↓
Analytics Automatically Update
```

For example:

```text
Account: FTMO Challenge
Account Size: $100,000

May 19
Daily P&L: +$450

May 20
Daily P&L: -$120

May 21
Daily P&L: +$700
```

The dashboard automatically calculates the account's updated performance from these daily entries.

## 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **SQLite**
* **Plotly**
* **Pandas**

The project keeps the data layer, calculations, analytics, and UI separated so individual components can be modified without restructuring the entire application.

## 🚀 Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<repository-name>.git
cd Trading-Journal
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py

On Windows, you can also run Streamlit directly through the virtual environment:
.\.venv\Scripts\streamlit.exe run app.py --server.headless true
```

The application will open in your browser.

## 💾 Data Storage

Trading Journal currently uses **SQLite** for local data storage.

The database stores account information and daily journal entries, including P&L, notes, and related data.

The local database file is created automatically when the application starts.

## 🔒 Privacy

Trading Journal is designed to keep your journal data under your control when running locally.

Avoid committing sensitive information such as:

* API keys
* Passwords
* Authentication tokens
* Private credentials
* Environment variables containing secrets

Add sensitive files to `.gitignore` before pushing the project to GitHub.

## 📌 Project Status

Trading Journal is actively being developed with a focus on creating a simple but powerful journaling experience for traders managing multiple accounts.

Future improvements may include:

* Advanced prop-firm rule tracking
* More analytics
* Account comparison
* Calendar heatmaps
* Exporting journal data
* Cloud database support
* Authentication and user accounts

---

**Trading Journal** — Track the day. Understand the performance. Improve the process.
v