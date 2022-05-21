FROM python:3.8-slim-buster

WORKDIR /flask-deploy

COPY . .
RUN apt-get -y update \
    && apt-get -y install python3-dev  \
    && apt-get -y install python3-setuptools  \
    && apt-get -y install build-essential libssl-dev libffi-dev

RUN pip install --upgrade pip \
    && pip install --no-cache-dir wheel \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["uwsgi", "app.ini"]