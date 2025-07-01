#!/usr/bin/env bash

echo "Running migrations and collecting static files..."
cd backend || exit
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
