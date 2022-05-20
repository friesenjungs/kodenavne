FROM python:3.8-slim-buster

WORKDIR /flask-deploy

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["uwsgi", "app.ini"]