#!/bin/bash

flask db init --directory ./migrations
flask db migrate
flask db upgrade

python app.py