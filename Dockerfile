FROM python:3.12-slim

WORKDIR /app

# Minimal runtime deps for opencv-python-headless / easyocr
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY detector/requirements.txt ./detector/requirements.txt
RUN pip install --no-cache-dir -r detector/requirements.txt

COPY detector ./detector
WORKDIR /app/detector

RUN useradd -m -u 10001 appuser \
  && mkdir -p /app/.cache \
  && chown -R appuser:appuser /app

ENV PORT=5000
ENV BASE_PATH=/detect
EXPOSE 5000

USER appuser
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--log-level", "info", "--workers", "1"]

