FROM python:3.8-slim-buster as backend-base

LABEL org.opencontainers.image.source = "https://github.com/friesenjungs/kodenavne"

COPY requirements.txt .

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends python3-dev  \
    && apt-get install -y --no-install-recommends python3-setuptools  \
    && apt-get install -y --no-install-recommends build-essential libssl-dev libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install --no-cache-dir wheel \
    && pip install --no-cache-dir -r ./requirements.txt

FROM backend-base

WORKDIR /flask-deploy

COPY . .

CMD ["bash", "./container-start-script.sh"]