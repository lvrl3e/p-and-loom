FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# Overridden at runtime to point at the mounted persistent disk (see render.yaml)
ENV TRADING_JOURNAL_DB=/data/trading_journal.db \
    TRADING_JOURNAL_UPLOADS=/data/uploads

EXPOSE 8501

CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true
