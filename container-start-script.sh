#!/bin/bash

flask db init --directory ./migrations
flask db migrate
flask db upgrade

case "${FLASK_ENV}" in
  production) uwsgi app.ini ;;
  development) python app.py ;;
  *) echo "FLASK_ENV value not allowed - use either production or development" ;;
esac