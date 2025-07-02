#!/usr/bin/env bash
pip install -r requirements.txt

cd backend || exit
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
