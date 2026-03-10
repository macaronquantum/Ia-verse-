FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential python3.11 python3-pip python3.11-venv && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python3.11 -m pip install --upgrade pip && python3.11 -m pip install -r requirements.txt
COPY . .
RUN mkdir -p /var/models /var/cache
CMD ["bash", "start.sh"]
