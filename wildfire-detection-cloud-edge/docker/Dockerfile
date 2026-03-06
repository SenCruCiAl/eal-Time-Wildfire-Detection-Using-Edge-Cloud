FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY edge /app/edge
COPY cloud /app/cloud
COPY ml /app/ml

# Default command runs edge camera pipeline; override in deployment as needed.
CMD ["python", "edge/camera_stream.py"]
