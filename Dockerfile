FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analytics_consumer.py .
COPY consumers consumers
COPY utils utils
COPY models models
COPY services services
COPY sql sql
COPY seed seed

ENV PYTHONPATH=/app

CMD ["python", "analytics_consumer.py"]