FROM python:3.11-slim

WORKDIR /app
ENV MOVIECLIPPER_CONFIG_DIR=/config

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt

VOLUME ["/config"]

COPY . .

CMD ["python", "run.py"]
