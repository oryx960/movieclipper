FROM python:3.11-slim

WORKDIR /app
ENV MOVIECLIPPER_CONFIG_DIR=/config

COPY requirements.txt .
RUN pip install -r requirements.txt

VOLUME ["/config"]

COPY . .

CMD ["python", "run.py"]
