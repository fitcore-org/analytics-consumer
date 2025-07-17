FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY analytics_consumer.py .
COPY wait-for-it.sh /wait-for-it.sh
COPY consumers consumers
COPY utils utils
COPY models models
RUN chmod +x /wait-for-it.sh

ENV PYTHONPATH=/app

CMD ["/wait-for-it.sh", "postgres:5432", "--", "python", "analytics_consumer.py"]