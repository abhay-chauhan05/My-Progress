FROM python:3.11-slim

# System libs for matplotlib / numpy wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Bind to all interfaces inside the container.
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
